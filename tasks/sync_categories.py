import ynab
import pandas as pd
import json
import os
import argparse
import curses
from os import environ as env
from pathlib import Path
from openai import OpenAI
from openai import OpenAI

from tasks.utils import align_ynab_categories


YNAB_BUDGET = "333be704-3f75-44fd-8dce-a074ac019854"


def file_cached(func):
    def wrapper(*args, **kwargs):
        cache_file = Path(f"{func.__name__}.json")
        if cache_file.exists():
            with open(cache_file, "r") as f:
                return json.load(f)
        result = func(*args, **kwargs)
        with open(cache_file, "w") as f:
            json.dump(result, f, indent=4)
        return result

    return wrapper


@file_cached
def match_with_ai(ynab_categories, plan_data):
    """
    Use OpenAI GPT-4 to semantically match YNAB categories with plan categories.
    The function sends YNAB and plan categories as JSON to the AI
    and forces a JSON response (with a strict template) containing mappings.
    Returns a dict of matches: { ynab_category_id: {ynab_name, ynab_group, plan_category, plan_group} }.
    """
    client = OpenAI(api_key=env.get("OPENAI_API_KEY"))

    # Build the prompt (using a strict JSON template)
    prompt = (
        ""
        "Each YNAB category is a JSON object with fields 'id', 'name', and 'group'. "
        "Each plan category is a JSON object with fields 'category' and 'group'. "
        "Using semantic similarity, determine the best match for each YNAB category. "
        "Here are the inputs:\n"
        "YNAB Categories: {ynab_json}\n"
        "Plan Categories: {plan_json}"
    )
    ynab_json = json.dumps(ynab_categories, indent=2)
    plan_json = json.dumps(plan_data, indent=2)
    full_prompt = prompt.format(ynab_json=ynab_json, plan_json=plan_json)

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": """
                        You are a helpful assistant that matches YNAB categories with plan categories. 
                        You are an expert in categorization and semantic matching.
                    """,
                },
                {"role": "user", "content": full_prompt},
            ],
            temperature=1,
            max_tokens=5000,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "Matching",
                    "strict": True,
                    "description": "A JSON object with matched categories",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "matches": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "ynab_id": {"type": "string"},
                                        "ynab_name": {"type": "string"},
                                        "ynab_group": {"type": "string"},
                                        "plan_category": {"type": "string"},
                                        "plan_group": {"type": "string"},
                                    },
                                    "required": [
                                        "ynab_id",
                                        "ynab_name",
                                        "ynab_group",
                                        "plan_category",
                                        "plan_group",
                                    ],
                                    "additionalProperties": False,
                                },
                            },
                            "unmatched": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                        "required": ["matches", "unmatched"],
                        "additionalProperties": False,
                    },
                },
            },
        )
        content = response.choices[0].message.content
        result = json.loads(content)
        return result.get("matches", {})
    except Exception as e:
        print("Error obtaining AI-based matches:", e)
        return {}


def get_original_index(sorted_index, index_mapping):
    """Convert a sorted index to original index using the mapping"""
    return index_mapping[sorted_index]


def draw_menu(
    stdscr,
    ynab_categories,
    plan_data,
    current_ynab_idx,
    current_plan_idx,
    matches,
    skipped,
    hidden,
    index_mapping,
):
    stdscr.clear()
    h, w = stdscr.getmaxyx()

    # Print header
    header = "Plan Categories vs YNAB Categories"  # Swapped order in title
    stdscr.addstr(0, (w - len(header)) // 2, header, curses.A_BOLD)

    # Instructions
    stdscr.addstr(
        1, 2, "Use UP/DOWN arrows to navigate, TAB to switch lists", curses.A_DIM
    )
    stdscr.addstr(
        2,
        2,
        "ENTER to match, 'S' to skip, 'H' to hide, 'D' to delete status",
        curses.A_DIM,
    )
    stdscr.addstr(3, 2, "Press 'I' for AI matching, 'Q' to save and quit", curses.A_DIM)

    # Draw middle divider
    middle = w // 2
    for y in range(5, h - 2):
        stdscr.addstr(y, middle, "│")

    # Draw column headers - SWAPPED
    stdscr.addstr(5, 2, "Plan Categories", curses.A_BOLD)  # Now on left
    stdscr.addstr(5, middle + 2, "YNAB Categories", curses.A_BOLD)  # Now on right

    # Draw Plan categories (now on the left)
    max_items = h - 8  # Available lines for items
    start_plan = max(0, current_plan_idx - max_items // 2)
    end_plan = min(len(plan_data), start_plan + max_items)

    for i, idx in enumerate(range(start_plan, end_plan)):
        y = 7 + i
        if y >= h - 2:
            break

        category_info = plan_data[idx]
        display = f"{category_info['group']} > {category_info['category']}"

        # Truncate if too long
        if len(display) > middle - 4:
            display = display[: middle - 7] + "..."

        attr = curses.A_NORMAL
        if idx == current_plan_idx:
            attr = curses.A_REVERSE

        # Check if this plan category is used in any match
        prefix = "  "
        is_matched = False
        for cat_id, match_info in matches.items():
            if (
                match_info["plan_category"] == category_info["category"]
                and match_info["plan_group"] == category_info["group"]
            ):
                prefix = "✓ "
                attr |= curses.A_BOLD
                is_matched = True
                break

        stdscr.addstr(y, 2, f"{prefix}{display}", attr)

    # Draw YNAB categories (now on the right)
    start_ynab = max(0, current_ynab_idx - max_items // 2)
    end_ynab = min(len(ynab_categories), start_ynab + max_items)

    for i, idx in enumerate(range(start_ynab, end_ynab)):
        y = 7 + i
        if y >= h - 2:
            break

        category = ynab_categories[idx]
        cat_id = category["id"]
        display = f"{category['group']} > {category['name']}"

        # Truncate if too long
        if len(display) > middle - 4:
            display = display[: middle - 7] + "..."

        attr = curses.A_NORMAL
        if idx == current_ynab_idx:
            attr = curses.A_REVERSE

        # Show matched, skipped, or hidden status
        prefix = "  "
        if cat_id in matches:
            prefix = "✓ "
            attr |= curses.A_BOLD
        elif cat_id in skipped:
            prefix = "✗ "
            attr |= curses.A_BOLD
        elif cat_id in hidden:
            prefix = "⚠ "
            attr |= curses.A_BOLD

        stdscr.addstr(y, middle + 2, f"{prefix}{display}", attr)

    # Status bar
    matches_count = len(matches)
    skipped_count = len(skipped)
    hidden_count = len(hidden)
    total_categories = len(ynab_categories)
    remaining = total_categories - matches_count - skipped_count - hidden_count
    status = f"Matched: {matches_count} | Skipped: {skipped_count} | Hidden: {hidden_count} | Remaining: {remaining} | Total: {total_categories}"
    stdscr.addstr(h - 1, 2, status)

    stdscr.refresh()


def interactive_matching(stdscr, ynab_categories_original, plan_data):
    # Initialization
    curses.curs_set(0)  # Hide cursor
    current_ynab_idx = 0
    current_plan_idx = 0
    focus_on_plan = True  # Default focus is now on Plan categories (left side)
    matches = {}  # {ynab_id: {ynab_name, ynab_group, plan_category, plan_group}}
    skipped = set()  # Set of skipped YNAB category IDs
    hidden = set()  # Set of hidden YNAB category IDs

    # Load existing matches if available
    output_path = Path("category_matches.json")
    if output_path.exists():
        try:
            with open(output_path, "r") as f:
                matches = json.load(f)
        except:
            pass

    # Load existing skipped and hidden categories if available
    skipped_path = Path("skipped_categories.json")
    if skipped_path.exists():
        try:
            with open(skipped_path, "r") as f:
                skipped = set(json.load(f))
        except:
            pass

    hidden_path = Path("hidden_categories.json")
    if hidden_path.exists():
        try:
            with open(hidden_path, "r") as f:
                hidden = set(json.load(f))
        except:
            pass

    # Align categories based on plan_data order
    ynab_categories, index_mapping = align_ynab_categories(
        ynab_categories_original, plan_data, matches, skipped, hidden
    )

    while True:
        draw_menu(
            stdscr,
            ynab_categories,
            plan_data,
            current_ynab_idx,
            current_plan_idx,
            matches,
            skipped,
            hidden,
            index_mapping,
        )

        key = stdscr.getch()

        if key == ord("q") or key == ord("Q"):
            # Save and exit
            return matches, skipped, hidden

        elif key == ord("i") or key == ord("I"):
            # Show message that AI is working
            h, w = stdscr.getmaxyx()
            stdscr.addstr(
                h - 1, 2, "AI is matching categories... please wait...", curses.A_BOLD
            )
            stdscr.refresh()

            try:
                # Call the AI matching function
                ai_matches = match_with_ai(ynab_categories_original, plan_data)

                # If we got matches, apply them
                if ai_matches:
                    for match_info in ai_matches:
                        # Don't overwrite existing matches unless they're from previous AI runs
                        cat_id = match_info["ynab_id"]
                        if cat_id not in matches or matches.get(cat_id, {}).get(
                            "ai_matched", False
                        ):
                            # Mark this as an AI-generated match for future reference
                            match_info["ai_matched"] = True
                            matches[cat_id] = match_info

                            # Remove from skipped/hidden if needed
                            if cat_id in skipped:
                                skipped.remove(cat_id)
                            if cat_id in hidden:
                                hidden.remove(cat_id)

                    # Resort categories after applying AI matches
                    ynab_categories, index_mapping = align_ynab_categories(
                        ynab_categories_original, plan_data, matches, skipped, hidden
                    )

                    # Show success message
                    stdscr.addstr(
                        h - 1,
                        2,
                        f"AI matched {len(ai_matches)} categories!        ",
                        curses.A_BOLD,
                    )
                else:
                    # Show no matches message
                    stdscr.addstr(
                        h - 1,
                        2,
                        "AI found no matches or encountered an error.",
                        curses.A_BOLD,
                    )

                stdscr.refresh()
                curses.napms(2000)  # Show message for 2 seconds

            except Exception as e:
                # Show error message
                error_msg = f"AI matching error: {str(e)[:50]}..."
                stdscr.addstr(h - 1, 2, error_msg, curses.A_BOLD)
                stdscr.refresh()
                curses.napms(2000)  # Show error for 2 seconds

        elif key == curses.KEY_LEFT:
            focus_on_plan = True
        elif key == curses.KEY_RIGHT:
            focus_on_plan = False

        elif key == curses.KEY_UP:
            if focus_on_plan:
                current_plan_idx = max(0, current_plan_idx - 1)
            else:
                current_ynab_idx = max(0, current_ynab_idx - 1)

        elif key == curses.KEY_DOWN:
            if focus_on_plan:
                current_plan_idx = min(len(plan_data) - 1, current_plan_idx + 1)
            else:
                current_ynab_idx = min(len(ynab_categories) - 1, current_ynab_idx + 1)

        elif key == 10:  # ENTER key
            if current_ynab_idx < len(ynab_categories) and current_plan_idx < len(
                plan_data
            ):
                ynab_cat = ynab_categories[current_ynab_idx]
                plan_cat_info = plan_data[current_plan_idx]

                # Create or update match
                cat_id = ynab_cat["id"]
                matches[cat_id] = {
                    "ynab_id": cat_id,
                    "ynab_name": ynab_cat["name"],
                    "ynab_group": ynab_cat["group"],
                    "plan_category": plan_cat_info["category"],
                    "plan_group": plan_cat_info["group"],
                }

                # Remove from skipped and hidden if it was there before
                if cat_id in skipped:
                    skipped.remove(cat_id)
                if cat_id in hidden:
                    hidden.remove(cat_id)

                # Resort the categories
                ynab_categories, index_mapping = align_ynab_categories(
                    ynab_categories_original, plan_data, matches, skipped, hidden
                )

                # Select the next plan category instead of next YNAB category
                if current_plan_idx < len(plan_data) - 1:
                    # Check if the current plan category is already used in any match
                    next_idx = current_plan_idx + 1
                    current_plan_idx = next_idx

                # After matching, focus on the plan categories
                focus_on_plan = False

        elif key == ord("s") or key == ord("S"):
            if not focus_on_plan and current_ynab_idx < len(ynab_categories):
                cat_id = ynab_categories[current_ynab_idx]["id"]

                # Mark as skipped
                skipped.add(cat_id)

                # Remove from matches and hidden if it was there before
                if cat_id in matches:
                    del matches[cat_id]
                if cat_id in hidden:
                    hidden.remove(cat_id)

                # Resort the categories
                ynab_categories, index_mapping = align_ynab_categories(
                    ynab_categories_original, plan_data, matches, skipped, hidden
                )

        elif key == ord("h") or key == ord("H"):
            if not focus_on_plan and current_ynab_idx < len(ynab_categories):
                cat_id = ynab_categories[current_ynab_idx]["id"]

                # Mark as hidden
                hidden.add(cat_id)

                # Remove from matches and skipped if it was there before
                if cat_id in matches:
                    del matches[cat_id]
                if cat_id in skipped:
                    skipped.remove(cat_id)

                # Resort the categories
                ynab_categories, index_mapping = align_ynab_categories(
                    ynab_categories_original, plan_data, matches, skipped, hidden
                )

        elif key == ord("d") or key == ord("D"):
            if not focus_on_plan and current_ynab_idx < len(ynab_categories):
                cat_id = ynab_categories[current_ynab_idx]["id"]

                # Remove all statuses
                if cat_id in matches:
                    del matches[cat_id]
                if cat_id in skipped:
                    skipped.remove(cat_id)
                if cat_id in hidden:
                    hidden.remove(cat_id)

                # Resort the categories
                ynab_categories, index_mapping = align_ynab_categories(
                    ynab_categories_original, plan_data, matches, skipped, hidden
                )


def sync_categories():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Match YNAB categories to plan categories from a CSV."
    )
    parser.add_argument(
        "--file",
        type=str,
        default="plan.csv",
        help="Path to the CSV file containing the plan categories.",
    )
    parser.add_argument(
        "--ai-match",
        action="store_true",
        help="Automatically perform AI matching before starting the interface",
    )
    args = parser.parse_args()

    csv_path = Path(args.file)

    if not csv_path.exists():
        print(f"Error: {csv_path} not found")
        return

    try:
        plan_df = pd.read_csv(csv_path)
        required_columns = ["category", "category_group"]
        missing_columns = [
            col for col in required_columns if col not in plan_df.columns
        ]

        if missing_columns:
            if "category_group" in missing_columns and "category" in plan_df.columns:
                print("Warning: 'category_group' column not found, using empty group")
                plan_df["category_group"] = ""
            else:
                print(
                    f"Error: The CSV must have these columns: {', '.join(required_columns)}"
                )
                return

        # Create a list of dictionaries with group and category
        plan_data = []
        for _, row in plan_df.iterrows():
            plan_data.append(
                {"group": row["category_group"], "category": row["category"]}
            )
    except Exception as e:
        print(f"Error reading {csv_path}: {e}")
        return

    # Get YNAB categories
    configuration = ynab.Configuration(access_token=env.get("YNAB_TOKEN"))
    ynab_categories = []

    try:
        with ynab.ApiClient(configuration) as client:
            categories_api = ynab.CategoriesApi(client)
            categories_response = categories_api.get_categories(YNAB_BUDGET)
            categories = categories_response.data.category_groups

            for category_group in categories:
                for category in category_group.categories:
                    ynab_categories.append(
                        {
                            "id": category.id,
                            "name": category.name,
                            "group": category_group.name,
                        }
                    )
    except Exception as e:
        print(f"Error fetching YNAB categories: {e}")
        return

    print(
        f"\nFound {len(ynab_categories)} YNAB categories and {len(plan_data)} plan categories"
    )

    # Perform AI matching if requested
    ai_matches = {}
    if args.ai_match and env.get("OPENAI_API_KEY"):
        print("Performing AI category matching...")
        try:
            ai_matches = match_with_ai(ynab_categories, plan_data)
            print(f"AI found {len(ai_matches)} potential matches")

            # Use these matches as a starting point for the interactive matching
            for cat_id, match_info in ai_matches.items():
                match_info["ai_matched"] = True

        except Exception as e:
            print(f"Error during AI matching: {e}")

    print("Starting interactive category matching...")

    # Start the interactive curses UI with AI matches pre-loaded
    if ai_matches:
        # Wrap the original function with a function that pre-loads AI matches
        def interactive_with_ai(stdscr, ynab_cats, plan_cats):
            nonlocal ai_matches
            # Initialize matches from AI matches
            current_ynab_idx = 0
            current_plan_idx = 0
            focus_on_plan = True
            matches = ai_matches
            skipped = set()
            hidden = set()

            # Align categories based on plan_data order
            sorted_cats, idx_mapping = align_ynab_categories(
                ynab_cats, plan_cats, matches, skipped, hidden
            )

            # Call the regular interactive_matching but with our own implementation
            # that starts with AI matches
            return interactive_matching(stdscr, ynab_cats, plan_cats)

        matches, skipped, hidden = curses.wrapper(
            interactive_with_ai, ynab_categories, plan_data
        )
    else:
        # Regular interactive matching without AI pre-matching
        matches, skipped, hidden = curses.wrapper(
            interactive_matching, ynab_categories, plan_data
        )

    # Save matches to JSON with detailed information
    output_path = Path("category_matches.json")
    try:
        with open(output_path, "w") as f:
            json.dump(matches, f, indent=4)

        print(f"\nCategory matches saved to {output_path}")
        print(
            f"Total matches: {len(matches)} out of {len(ynab_categories)} YNAB categories"
        )

        # Save skipped categories (just IDs)
        skipped_path = Path("skipped_categories.json")
        with open(skipped_path, "w") as f:
            json.dump(list(skipped), f, indent=4)
        print(f"Skipped categories: {len(skipped)} (IDs saved to {skipped_path})")

        # Save hidden categories (just IDs)
        hidden_path = Path("hidden_categories.json")
        with open(hidden_path, "w") as f:
            json.dump(list(hidden), f, indent=4)
        print(f"Hidden categories: {len(hidden)} (IDs saved to {hidden_path})")

        # Create a combined report with all details and proper ordering
        # First, create a dictionary of all YNAB categories for reference
        all_ynab_cats = {
            cat["id"]: {"name": cat["name"], "group": cat["group"]}
            for cat in ynab_categories
        }

        # Create an ordered list of categories with status
        ordered_categories = []

        # First, add all matched categories in their original order
        for cat in ynab_categories:
            cat_id = cat["id"]
            if cat_id in matches:
                ordered_categories.append(
                    {
                        "id": cat_id,
                        "name": cat["name"],
                        "group": cat["group"],
                        "status": "matched",
                        "match_details": matches[cat_id],
                    }
                )

        # Then add all regular (unprocessed) categories
        for cat in ynab_categories:
            cat_id = cat["id"]
            if cat_id not in matches and cat_id not in skipped and cat_id not in hidden:
                ordered_categories.append(
                    {
                        "id": cat_id,
                        "name": cat["name"],
                        "group": cat["group"],
                        "status": "unprocessed",
                    }
                )

        # Then add all skipped categories
        for cat in ynab_categories:
            cat_id = cat["id"]
            if cat_id in skipped:
                ordered_categories.append(
                    {
                        "id": cat_id,
                        "name": cat["name"],
                        "group": cat["group"],
                        "status": "skipped",
                    }
                )

        # Finally add all hidden categories
        for cat in ynab_categories:
            cat_id = cat["id"]
            if cat_id in hidden:
                ordered_categories.append(
                    {
                        "id": cat_id,
                        "name": cat["name"],
                        "group": cat["group"],
                        "status": "hidden",
                    }
                )

        # Create the final report
        report = {
            "ordered_categories": ordered_categories,
            "matches": matches,
            "skipped": list(skipped),
            "hidden": list(hidden),
            "ynab_categories": all_ynab_cats,
            "stats": {
                "total": len(ynab_categories),
                "matched": len(matches),
                "skipped": len(skipped),
                "hidden": len(hidden),
                "unprocessed": len(ynab_categories)
                - len(matches)
                - len(skipped)
                - len(hidden),
            },
        }

        with open("category_sync_report.json", "w") as f:
            json.dump(report, f, indent=4)
        print("Complete report saved to category_sync_report.json")

    except Exception as e:
        print(f"Error saving results: {e}")


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    sync_categories()

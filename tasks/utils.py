def sort_ynab_categories(ynab_categories, matches, skipped, hidden):
    """Sort categories according to display rules:
    1. Matched categories first (preserving original order)
    2. Regular categories (no status)
    3. Skipped categories
    4. Hidden categories

    Returns sorted categories and index mapping (new_index -> original_index)
    """
    # Create categories with their status and original index
    categorized = []
    for idx, cat in enumerate(ynab_categories):
        cat_id = cat["id"]
        status = "regular"
        if cat_id in matches:
            status = "matched"
        elif cat_id in skipped:
            status = "skipped"
        elif cat_id in hidden:
            status = "hidden"

        categorized.append({"original_idx": idx, "category": cat, "status": status})

    # Custom sort function to prioritize matched, then regular, then skipped, then hidden
    def sort_key(item):
        status_order = {"matched": 0, "regular": 1, "skipped": 2, "hidden": 3}
        # Use status order as primary key and original index as secondary key
        return (status_order[item["status"]], item["original_idx"])

    # Sort the categories
    sorted_cats = sorted(categorized, key=sort_key)

    # Create the mapping dictionary and sorted category list
    sorted_categories = []
    index_mapping = {}  # new_index -> original_index

    for new_idx, item in enumerate(sorted_cats):
        sorted_categories.append(item["category"])
        index_mapping[new_idx] = item["original_idx"]

    return sorted_categories, index_mapping


def align_ynab_categories(ynab_categories, plan_data, matches, skipped, hidden):
    """
    Align YNAB categories so that if a category is matched to a plan item (by group and category),
    it appears on the same row as the plan row. For plan rows without a match, assign the next
    unmatched YNAB category. Any remaining unmatched YNAB categories are appended at the end.

    Returns:
        aligned_categories: list of YNAB category dicts (or {} as placeholder)
        index_mapping: dict mapping new index -> original index in ynab_categories
    """
    # Build mapping from plan tuple to matched YNAB category
    plan_to_matched = {}
    for y in ynab_categories:
        yid = y.get("id")
        if yid in matches:
            mi = matches[yid]
            key = (mi.get("plan_group", ""), mi.get("plan_category", ""))
            plan_to_matched[key] = y

    # Create list of unmatched YNAB categories
    unmatched = [y for y in ynab_categories if y.get("id") not in matches]

    aligned = []
    index_mapping = {}
    used_ids = set()
    # Iterate over plan_data order
    for i, plan in enumerate(plan_data):
        key = (plan.get("group", ""), plan.get("category", ""))
        if key in plan_to_matched:
            cat = plan_to_matched[key]
            aligned.append(cat)
            used_ids.add(cat["id"])
            orig_idx = next(
                idx for idx, y in enumerate(ynab_categories) if y.get("id") == cat["id"]
            )
            index_mapping[len(aligned) - 1] = orig_idx
        else:
            # If available, take the next unmatched category
            candidate = None
            for cand in unmatched:
                if cand["id"] not in used_ids:
                    candidate = cand
                    break
            if candidate:
                aligned.append(candidate)
                used_ids.add(candidate["id"])
                orig_idx = next(
                    idx
                    for idx, y in enumerate(ynab_categories)
                    if y.get("id") == candidate["id"]
                )
                index_mapping[len(aligned) - 1] = orig_idx
            else:
                aligned.append({})  # placeholder if no candidate available
                index_mapping[len(aligned) - 1] = -1
    # Append any remaining unmatched YNAB categories
    for cand in unmatched:
        if cand["id"] not in used_ids:
            aligned.append(cand)
            orig_idx = next(
                idx
                for idx, y in enumerate(ynab_categories)
                if y.get("id") == cand["id"]
            )
            index_mapping[len(aligned) - 1] = orig_idx

    return aligned, index_mapping

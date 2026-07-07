from neuro_san.interfaces.coded_tool import CodedTool

class IdentityResolverTool(CodedTool):
    async def async_invoke(self, args, sly_data):
        top_n = int(args.get("top_n", 3))
        ranked_ids_raw = args.get("candidate_ids", "")

        # Handle both comma-separated string and list
        if isinstance(ranked_ids_raw, list):
            ranked_ids = ranked_ids_raw
        else:
            ranked_ids = [x.strip() for x in ranked_ids_raw.split(",") if x.strip()]

        approved = ranked_ids[:top_n]
        sealed_count = len(ranked_ids) - len(approved)

        resolved = []
        for cid in approved:
            identity = sly_data.get(cid, {})
            resolved.append({
                "candidate_id": cid,
                "name": identity.get("name", "Unknown"),
                "resume_id": identity.get("resume_id", "Unknown")
            })

        print(f"[BLINDSPOT] {len(resolved)} identities released. "
              f"{sealed_count} candidates permanently sealed.")

        return {
            "approved_candidates": resolved,
            "sealed_count": sealed_count
        }
from neuro_san.interfaces.coded_tool import CodedTool

INTERVIEWER_SLOTS = [
    "Tue 11:00 AM", "Tue 3:00 PM",
    "Wed 10:00 AM", "Wed 4:30 PM",
    "Thu 2:00 PM"
]

CANDIDATE_SLOTS = [
    "Mon 5:00 PM", "Tue 3:00 PM",
    "Wed 10:00 AM", "Wed 1:00 PM",
    "Fri 11:00 AM"
]

class AvailabilityMatcherTool(CodedTool):
    async def async_invoke(self, args, sly_data):
        candidate_name = args.get("candidate_name", "Candidate")

        # Pure calendar math — no LLM doing this
        overlap = next(
            (slot for slot in CANDIDATE_SLOTS
             if slot in INTERVIEWER_SLOTS),
            "No overlapping slot found"
        )

        print(f"[BLINDSPOT] Slot matched for {candidate_name}: {overlap}")

        return {
            "candidate": candidate_name,
            "proposed_slot": overlap,
            "interviewer_slots": INTERVIEWER_SLOTS,
            "candidate_slots": CANDIDATE_SLOTS
        }
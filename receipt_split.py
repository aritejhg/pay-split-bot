from collections import defaultdict

class ReceiptSplit:
    def __init__(self, chat_id, message_id, items) -> None:
        self.chat_id = chat_id
        self.message_id = message_id
        self.items = items
        self.responses = {}

    def update_response(self, user_name, option_ids):
        self.responses[user_name] = option_ids

    def get_summary(self):
        user_sumamries = defaultdict(dict)
        for user, options in self.responses.items():
            if len(options) == 0:
                continue
            summ = user_sumamries[user]
            summ["items"] = (self.items[ind] for ind in options)
            summ["total"] = 100

        out = "*Split Summary*\n"
        for user, summary in user_sumamries.items():
            out = out + f'\n{user} - {summary["total"]}'
            for i, item in enumerate(summary["items"]):
                out = out + f"\n{i+1}. {item}"
                out = out + "\n"

        return out

    def __repr__(self) -> str:
        return str(self.responses)
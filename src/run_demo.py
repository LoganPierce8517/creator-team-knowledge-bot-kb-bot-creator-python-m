from kb_bot import KnowledgeBot, should_escalate


def main() -> None:
    bot = KnowledgeBot()
    bot.add_documents([
        {"id": "delivery-1", "title": "Delivery", "text": "Digital downloads are signed for 24 hours after purchase."},
        {"id": "subscriber-1", "title": "Subscribers", "text": "Weekly subscriber updates go out every Friday at 10:00."},
        {"id": "processing-1", "title": "Processing", "text": "New uploads are processed into an MP4 preview before review."},
    ])
    result = bot.answer("When do subscriber updates go out?")
    print(result["answer"])
    print("Escalate:", should_escalate(result))


if __name__ == "__main__":
    main()

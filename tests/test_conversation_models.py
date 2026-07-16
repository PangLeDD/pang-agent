import unittest

from app.models.conversation import Conversation, ConversationMessage


class ConversationModelsTest(unittest.TestCase):
    def test_conversation_tables_are_mapped(self):
        self.assertEqual(Conversation.__tablename__, "conversations")
        self.assertIn("user_id", Conversation.__table__.c)
        self.assertIn("conversation_id", ConversationMessage.__table__.c)

    def test_conversation_message_fk_points_to_conversations(self):
        fk_column = ConversationMessage.__table__.c.conversation_id
        fk = fk_column.foreign_keys.pop()
        self.assertEqual(fk.column.table.name, "conversations")
        self.assertEqual(fk.column.name, "id")

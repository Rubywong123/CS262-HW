import unittest
from unittest.mock import patch, MagicMock
import sqlite3
from db_viewer import show_db_content

class TestDBViewer(unittest.TestCase):
    @patch("sqlite3.connect")
    def test_show_db_content(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        mock_cursor.fetchall.side_effect = [[("users",), ("messages",)],
                                            [("user1", "hashed_pass"), ("user2", "hashed_pass2")],
                                            [(1, "user1", "user2", "Hello", "unread")]]
        
        with patch("builtins.print") as mock_print:
            show_db_content("test.db")
            
            # Verify that the cursor executed queries correctly
            mock_cursor.execute.assert_any_call("SELECT name FROM sqlite_master WHERE type='table'")
            mock_cursor.execute.assert_any_call("SELECT * FROM users")
            mock_cursor.execute.assert_any_call("SELECT * FROM messages")
            
            # Verify expected print output
            mock_print.assert_any_call("\nTable: users")
            mock_print.assert_any_call(("user1", "hashed_pass"))
            mock_print.assert_any_call(("user2", "hashed_pass2"))
            mock_print.assert_any_call("\nTable: messages")
            mock_print.assert_any_call((1, "user1", "user2", "Hello", "unread"))
        
        # Ensure connection is closed
        mock_conn.close.assert_called_once()

if __name__ == "__main__":
    unittest.main()
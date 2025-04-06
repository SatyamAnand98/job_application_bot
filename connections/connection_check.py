import os
from datetime import datetime

class FileHandler:
    _DAILY_LIMIT = 10
    _WEEKLY_LIMIT = 70
    
    def __init__(self):
        self._count_file_name = "./connections/connections_monitor.txt"
        self._today_date = datetime.now().strftime("%Y-%m-%d")  # Returns today's date in format "YYYY-MM-DD"
        self._week_number = datetime.now().strftime("%Y-%U")  # Format: "YYYY-WW"
        self._daily_count = 0
        self._weekly_count = 0
        self._last_run_date = None
        self._requested_connections = []
        self._read_file()
        
    def _read_file(self):
        if not os.path.exists(self._count_file_name):
            with open(self._count_file_name, "w") as f:
                f.write(f"last_run_date: {self._today_date}\n")# Write the current date to the file
                f.write(f"weekly_count {self._week_number}: 0\n")# Write the current week number and counts to the file
                f.write(f"requested_connections: \n")# Write the current requested connections to the file
                f.write(f"daily_count {self._today_date}: 0\n")# Write the current daily count to the file
        else:
            with open(self._count_file_name, "r") as f:
                lines = f.readlines()
                for line in lines:
                    if line.startswith("last_run_date:"):
                        self._last_run_date = line.strip().split(": ")[1]
                    elif line.startswith("weekly_count"):
                        if self._week_number in line:
                            self._weekly_count = int(line.strip().split(": ")[1])
                        else:
                            self._weekly_count = 0
                    elif line.startswith("requested_connections:"):
                        try:
                            self._requested_connections = line.strip().split(": ")[1].split(",")
                        except IndexError:
                            self._requested_connections = []
                    elif line.startswith(f"daily_count"):
                        if self._today_date in line:
                            self._daily_count = int(line.strip().split(": ")[1])
                        else:
                            self._daily_count = 0
    
    def update_requested_connections(self, user_name):
        if self._validate_user(user_name) and self._validate_counts():
            self._requested_connections = self._requested_connections + [user_name]
            
            with open(self._count_file_name, "w") as f:
                f.write(f"last_run_date: {self._today_date}\n")
                f.write(f"weekly_count {self._week_number}: {self._weekly_count}\n")
                f.write(f"requested_connections: {','.join(self._requested_connections)}\n")
                f.write(f"daily_count {self._today_date}: {self._daily_count}\n")
            
    def update_daily_count(self, count):
        if self._validate_counts():
            self._daily_count = self._daily_count + count
            self._weekly_count = self._weekly_count + count
            with open(self._count_file_name, "r") as f:
                lines = f.readlines()

            updated_lines = []
            for line in lines:
                if line.startswith("daily_count"):
                    if self._today_date in line:
                        # Update the daily count for the same date
                        updated_lines.append(f"daily_count {self._today_date}: {self._daily_count}\n")
                    else:
                        # Replace the date with today's date
                        updated_lines.append(f"daily_count {self._today_date}: {self._daily_count}\n")
                elif line.startswith("last_run_date:"):
                    updated_lines.append(f"last_run_date: {self._today_date}\n")
                elif line.startswith("weekly_count"):
                    if self._week_number in line:
                        # Update the weekly count for the same week number
                        updated_lines.append(f"weekly_count {self._week_number}: {self._weekly_count}\n")
                    else:
                        updated_lines.append(f"weekly_count {self._week_number}: {self._weekly_count}\n")
                elif line.startswith("requested_connections:"):
                    updated_lines.append(f"requested_connections: {','.join(self._requested_connections)}\n")
                else:
                    updated_lines.append(line)

            with open(self._count_file_name, "w") as f:
                f.writelines(updated_lines)
            
    def _get_requested_connections(self):
        return self._requested_connections
    
    def _get_daily_count(self):
        return self._daily_count
    
    def _get_weekly_count(self):
        return self._weekly_count
    
    def _validate_user(self, user_name):
        # Placeholder for user validation logic
        if user_name in self._requested_connections:
            raise Exception("User already exists in requested connections.")
        else:
            return True
    
    def _validate_counts(self):
        if self._daily_count >= self._DAILY_LIMIT or self._weekly_count >= self._WEEKLY_LIMIT:
            raise Exception("Daily or weekly limit reached.")
        else:
            return True
    
    
# if __name__ == "__main__":
    
#     file_handler = FileHandler()
#     try:
#         for i in range(20, 31):
#             file_handler.update_requested_connections(f"user{i}")
#             file_handler.update_daily_count(1)
#             print("Requested Connections:", file_handler._get_requested_connections())
#             print("Daily Count:", file_handler._get_daily_count())
#             print("Weekly Count:", file_handler._get_weekly_count())
#     except Exception as e:
#         print(f"An error occurred: {e}")
        
        
connection_monitor = FileHandler()
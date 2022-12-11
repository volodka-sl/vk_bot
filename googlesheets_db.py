"""
SPREADSHEET LINK: https://docs.google.com/spreadsheets/d/1TopREKBJKLRchXZsLAygIRnPoA1ZUOZWm7S3BIPC-Ws/edit#gid=0
"""

import gspread


class GoogleSpreadsheet(object):
    def __init__(self, spreadsheet_name, creds_name):
        self.sa = gspread.service_account(filename=creds_name)
        self.spreadsheet = self.sa.open(spreadsheet_name)

    def add_user(self, list_name, name, surname, user_id, city):
        worksheet = self.spreadsheet.worksheet(list_name)
        worksheet.add_rows(1)
        count_of_rows = worksheet.row_count + 1
        worksheet.update(f"A{count_of_rows}:D{count_of_rows}", [[name, surname, user_id, city]])

    def get_all_users_ids(self, list_name):
        worksheet = self.spreadsheet.worksheet(list_name)
        ids = worksheet.get("C2:C")

        return [a for b in ids for a in b]

    def get_user_city(self, list_name, user_id):
        worksheet = self.spreadsheet.worksheet(list_name)
        users = worksheet.get("C2:D")
        for user in users:
            if user[0] == user_id:
                return user[1]

    def change_user_city(self, list_name, user_id, new_city):
        worksheet = self.spreadsheet.worksheet(list_name)
        users_ids = self.get_all_users_ids(list_name)
        user_index = users_ids.index(user_id) + 2
        worksheet.update(f"D{user_index}", new_city)

    def get_top_posters(self, list_name, day, user_city):
        worksheet = self.spreadsheet.worksheet(list_name)
        worksheet.sort((6, "asc"), range=f"A2:F{worksheet.row_count}")
        result = []
        posters = worksheet.get("A2:E")
        for poster in posters:
            if len(result) < 5:
                if poster[3] == user_city and poster[4].split(" ")[0] == day:
                    result.append([poster[0], poster[1], poster[2]])

        resp = ""
        for poster in result:
            resp += f"'{poster[0]}' за {poster[1]} рублей: {poster[2]}\n"

        if resp:
            return resp
        return "Кажется, на твой город нет актуального расписания афиш :("

    def get_traffic_jam_stats(self, list_name, city):
        worksheet = self.spreadsheet.worksheet(list_name)
        traffic_jam_stats = worksheet.get_all_values()
        for stat in traffic_jam_stats:
            if stat[0] == city:
                return f"В городе {city} сейчас {stat[1]} баллов по нагруженности дорог"
        return "Похоже, по нагруженности твоего города нет информации :("

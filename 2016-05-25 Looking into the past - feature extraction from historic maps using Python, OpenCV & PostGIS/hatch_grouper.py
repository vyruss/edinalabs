import string
import datetime

from snaql.factory import Snaql

import pg_connection as u

"""
    assemble features in a polyline dataset into groups where group membership
    is based on all members being within a certain distance of one other, being
    spatially disjoint and having roughly the same orientation
"""


class LineGrouper(object):
    def __init__(self, table_name, db_connection_string, refresh=True,
                 search_distance=2.0, search_angle_delta=5.0):
        self.table_name = table_name
        self.db_connection_string = db_connection_string

        if refresh:
            # by default, we clear any groups assigned to lines
            self.reset_table()

        # parameters that control group membership
        self.search_distance = search_distance
        self.search_angle_delta = search_angle_delta

        # list of ungrouped line ids that will shrink over time
        self.ungrouped_line_ids = self.get_line_ids()

        # id to mark group membership
        self.group_id = 1

        snaql_factory = Snaql(".", "sql")
        self.queries = snaql_factory.load_queries("adrc_queries.sql")

    def search_for_neighbour(self, id, search_right="True"):
        """
        find the immediate neighbour of a line subject to various criteria
        """

        if search_right == "True":
            sql = self.queries.get_neighbour(
                srcTableName=self.table_name,
                id=id,
                searchDistance=self.search_distance,
                searchAngleDelta=self.search_angle_delta,
                searchDirection = ">"
            )
        else:
            sql = self.queries.get_neighbour(
                srcTableName=self.table_name,
                id=id,
                searchDistance=self.search_distance,
                searchAngleDelta=self.search_angle_delta,
                searchDirection = "<"
            )

        neighbour_id = None
        rs = u.query_pg(sql, self.db_connection_string)

        if len(rs) > 0:
            for r in rs:
                neighbour_id = r[0]

        return neighbour_id

    def get_line_ids(self):
        """
        get the id of all lines where group_id is 0
        the count of these will decrease over time as more lines are assigned to
        groups

        :return:
        """

        line_ids = None

        sql = self.queries.get_ungrouped_lines(
            table_name = self.table_name
        )

        rs = u.query_pg(sql, self.db_connection_string)
        if len(rs) > 0:
            line_ids = [i[0] for i in rs]

        return line_ids

    def group_lines(self, start_line_id, group_id):

        id_to_search_from = start_line_id
        self.update_table(start_line_id, group_id)

        num_lines_grouped = 1

        # expand right
        while id_to_search_from is not None:
            neighbour_id = self.search_for_neighbour(
                id=id_to_search_from
            )

            if neighbour_id is None:
                id_to_search_from = None
            else:
                self.ungrouped_line_ids.remove(neighbour_id)
                self.update_table(neighbour_id, group_id)
                num_lines_grouped += 1
                id_to_search_from = neighbour_id

        # reset the start line and expand left
        id_to_search_from = start_line_id
        while id_to_search_from is not None:
            neighbour_id = self.search_for_neighbour(
                id=id_to_search_from,
                search_right="False"
            )

            if neighbour_id is None:
                id_to_search_from = None
            else:
                self.ungrouped_line_ids.remove(neighbour_id)
                self.update_table(neighbour_id, group_id)
                num_lines_grouped += 1
                id_to_search_from = neighbour_id

        return num_lines_grouped

    def select_groups_into_new_table(self):

        sql = self.queries.drop_table(
            table_name = "".join([self.table_name, "_selection_4"])
        )
        u.update_pg(sql, self.db_connection_string)

        sql = self.queries.select_groups_into_new_table(
            srcTableName = self.table_name,
            destTableName = "".join([self.table_name, "_selection_4"])
        )
        u.update_pg(sql, self.db_connection_string)

    def reset_table(self):

        print("resetting table")

        sql = self.queries.reset_groups(
            table_name = self.table_name
        )
        u.update_pg(sql, self.db_connection_string)

    def update_table(self, gid, group_id):
        sql = self.queries.set_group_id(
            tableName=self.table_name,
            groupId=group_id,
            gid=gid
        )
        u.update_pg(sql, self.db_connection_string)

    def process_all(self):
        start_time = str(datetime.datetime.now())
        total_number_of_lines = len(self.ungrouped_line_ids)
        total_number_of_lines_grouped = 0

        while len(self.ungrouped_line_ids) > 0:
            start_line_id = self.ungrouped_line_ids[0]
            self.ungrouped_line_ids.remove(start_line_id)

            print("".join(["HERE:", str(start_line_id)]))

            number_of_lines_grouped = self.group_lines(start_line_id, self.group_id)
            total_number_of_lines_grouped += number_of_lines_grouped

            #TODO - provide more useful progress info
            print("".join(["Now allocated ", total_number_of_lines_grouped, " of ", total_number_of_lines, " lines to groups"]))

            self.group_id += 1

        end_time = str(datetime.datetime.now())

        print("".join(["Started at ", start_time]))
        print("".join(["Finished at ", end_time]))

    def process_one(self, id_to_process):
        lines_in_group = self.group_lines(id_to_process, self.group_id)


def main():

    if db_connection_string is not None:
        g = LineGrouper(
            table_name="adrc.big_thresholded_lines_sample",
            db_connection_string=db_connection_string,
            search_distance=2.5,
            search_angle_delta=10.0
        )

        g.process_all()
        g.select_groups_into_new_table()


if __name__ == "__main__":
    db_host = "localhost"
    db_port = "5432"
    db_name = "james"
    db_user = "james"

    db_params = u.DatabaseConnectionParams(
        host=db_host,
        port=db_port,
        dbname=db_name,
        user=db_user)

    db_connection_string = db_params.get_connection_string()

    if db_connection_string is not None:
        main()
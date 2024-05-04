class User:
    def __init__(self, user_id, preferences, visited_places):
        """
        Args:
            user_id (int): The id of the user.
            preferences (list): A list of strings representing the user's preferences.
            visited_places (list): A list of strings representing the places the user has visited.
        """
        self.user_id = user_id
        self.preferences = preferences
        self.visited_places = visited_places

    def update_preferences(self, new_preferences):
        """
        Update the user's preferences with new preferences.
        """
        self.preferences.update(new_preferences)

    def add_visited_place(self, place):
        """
        Add a place to the list of visited places.
        """
        if place not in self.visited_places:
            self.visited_places.append(place)

    def calculate_user_similarity(self, other_user):
        """
        Calculate the similarity between this user and another user in order to possibly create friend recommendations.
        """
        return len(set(self.preferences).intersection(other_user.preferences))
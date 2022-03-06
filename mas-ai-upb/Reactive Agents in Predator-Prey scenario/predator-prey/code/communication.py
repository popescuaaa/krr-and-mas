from base import Action

class AgentMessage(object):

    def __init__(self, sender_id, destination_id, content):
        self.sender_id = sender_id
        self.destination_id = destination_id
        self.content = content

    @staticmethod
    def filter_messages_for(all_messages, agent):
        """
        helper method to filter from a set of messages only those for a specified agent.
        :param all_messages: the messages to filter.
        :param agent: the destination agent
        :return: messages for the specified destination
        """
        return [msg for msg in all_messages if msg.destination_id == agent.id]


class SocialAction(Action):

    def __init__(self, physical_action):
        """
        Initialize a social action
        :param physical_action: the physical action the agent wants to perform
        """
        self.action = physical_action

        ## the set of outgoing messages, initially empty
        self.outgoing_messages = []


    def add_outgoing_message(self, sender_id, destination_id, content):
        self.outgoing_messages.append(AgentMessage(sender_id, destination_id, content))



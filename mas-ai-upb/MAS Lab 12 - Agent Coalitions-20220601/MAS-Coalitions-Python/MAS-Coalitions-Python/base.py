from typing import List, Dict, Any, Tuple


class Product(object):
    def __init__(self, type: str, value: float, price: float):
        self.type = type
        self.value = value
        self.price = price


class Coalition(object):
    MEMBER = "member"
    SHARE = "share"

    PROD_TYPE = "type"
    PROD_CONTRIB = "contrib"
    PROD_VALUE = "value"

    def __find_member(self, agent: "CoalitionAgent") -> Dict[str, Any] or None:
        for md in self.member_data:
            if agent == md[Coalition.MEMBER]:
                return md
        return None

    def __get_max_value_product(self, prod_type: str) -> Product or None:
        max_value = 0
        max_value_product = None

        for prod in self.products:
            if prod.type == prod_type and prod.value > max_value:
                max_value = prod.value
                max_value_product = prod

        return max_value_product

    def __get_product_stats(self) -> Tuple[Dict[str, List[float]], Dict[str, List[float]]]:
        product_contributions = {}
        product_values = {}

        for prod in self.products:
            contribs: List[float] = []
            vals: List[float] = []

            for md in self.member_data:
                contribs.append(md[Coalition.SHARE][prod.type][Coalition.PROD_CONTRIB])
                vals.append(md[Coalition.SHARE][prod.type][Coalition.PROD_VALUE])

            product_contributions[prod.type] = contribs
            product_values[prod.type] = vals

        return product_contributions, product_values

    def __build_share(self, share: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
        share_spec = {}

        product_types = [prod.type for prod in self.products]
        for prod_type in product_types:
            prod = self.__get_max_value_product(prod_type)
            prod_share = share.get(prod_type, None)

            if prod_share:
                if prod_share[Coalition.PROD_VALUE] < prod.value:
                    share_spec[prod_type] = prod_share
                else:
                    raise ValueError("Expected agent value for product type %s cannot exceed maximum possible "
                                     "product value %4.2f" % (prod_type, prod.value))
            else:
                share_spec[prod_type] = {
                    Coalition.PROD_CONTRIB: .0,
                    Coalition.PROD_VALUE: .0
                }

        return share_spec

    def __init__(self, products: List[Product]):
        self.products = products
        self.member_data = []

    def set_agent(self, agent: "CoalitionAgent", share: Dict[str, Dict[str, float]]):
        existing_md = self.__find_member(agent)

        if not existing_md:
            self.member_data.append({
                Coalition.MEMBER: agent,
                Coalition.SHARE: self.__build_share(share)
            })
        else:
            existing_md[Coalition.SHARE] = self.__build_share(share)

    def remove_agent(self, agent: "CoalitionAgent"):
        existing_md = self.__find_member(agent)
        self.member_data.remove(existing_md)

    def get_members(self) -> List["CoalitionAgent"]:
        return [md[Coalition.MEMBER] for md in self.member_data]

    def coalition_value(self) -> float:
        prod_contributions = dict([(prod.type, 0) for prod in self.products])
        product_types = set([prod.type for prod in self.products])

        for md in self.member_data:
            member_share = md[Coalition.SHARE]
            for prod_type in product_types:
                prod_contributions[prod_type] += member_share[prod_type][Coalition.PROD_CONTRIB]

        coalition_val = 0
        max_prod_values = dict([(prod.type, 0) for prod in self.products])

        for prod in self.products:
            prod_contrib = prod_contributions[prod.type]
            if prod_contrib >= prod.price and prod.value > max_prod_values[prod.type]:
                max_prod_values[prod.type] = prod.value

        for prod_type, prod_val in max_prod_values.items():
            if prod_val <= 0:
                return 0
            else:
                coalition_val += prod_val

        return coalition_val


    def coalition_valid(self) -> bool:
        prod_values = dict([(prod.type, 0) for prod in self.products])
        for md in self.member_data:
            member_share = md[Coalition.SHARE]
            for prod in self.products:
                prod_values[prod.type] += member_share[prod.type][Coalition.PROD_VALUE]

        for prod in self.products:
            prod_val = prod_values[prod.type]
            if prod_val > prod.value:
                return False

        return True


    def get_leader(self) -> "CoalitionAgent":
        max_contrib = 0
        leader = None

        for md in self.member_data:
            agent_contrib = 0
            for prod in self.products:
                agent_contrib += md[Coalition.SHARE][prod.type][Coalition.PROD_CONTRIB]

            if agent_contrib > max_contrib:
                max_contrib = agent_contrib
                leader = md[Coalition.MEMBER]

        return leader

    def is_member(self, agent: "CoalitionAgent") -> bool:
        for md in self.member_data:
            if md[Coalition.MEMBER] == agent:
                return True
        return False


    def __str__(self):
        res = ""
        res += "COALITION LEAD BY AGENT: %s \n" % str(self.get_leader())

        res += "\t" + "MEMBERS:" + "\n"
        for md in self.member_data:
            res += "\t" + "\t" + "[" + md[Coalition.MEMBER].name + " "
            for prod_type in md[Coalition.SHARE]:
                res += prod_type + "_contrib=" + "%4.2f" % md[Coalition.SHARE][prod_type][Coalition.PROD_CONTRIB] + " "
                res += prod_type + "_val=" + "%4.2f" % md[Coalition.SHARE][prod_type][Coalition.PROD_VALUE] + " "
            res += "]" + "\n"

        prod_contribs, prod_vals = self.__get_product_stats()

        res += "\n"
        res += "\t" + "PROD CONTRIBS:" + "\n"
        for prod_type in prod_contribs:
            res += "\t" + "\t" + prod_type + ": " + " ".join("%4.2f" % contrib for contrib in prod_contribs[prod_type])
            res += "\n"
            res += "\t" + "\t" + "Total: " + "%4.2f" % sum(prod_contribs[prod_type])
            res += "\n"

        res += "\n"
        res += "\t" + "PROD VALUES:" + "\n"
        for prod_type in prod_vals:
            res += "\t" + "\t" + prod_type + ": " + " ".join("%4.2f" % value for value in prod_vals[prod_type])
            res += "\n"
            res += "\t" + "\t" + "Total: " + "%4.2f" % sum(prod_vals[prod_type])
            res += "\n"

        return res

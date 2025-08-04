import xml.etree.ElementTree as ET
from pathlib import Path


class XMLCleaner:
    def __init__(self, xml) -> None:
        if isinstance(xml, str):
            self.et = ET.ElementTree(ET.fromstring(xml))
        elif isinstance(xml, Path):
            self.et = ET.parse(xml)
        self.w = int(self.et.getroot().attrib["width"])
        self.h = int(self.et.getroot().attrib["height"])

    def _filter_elements(self) -> list[ET.Element]:
        """return a list of elements that have the specified attributes

        Returns:
            list[ET.Element]: a list of elements that have the specified attributes
        """

        elements = []

        for ele in self.et.iter():
            if "bounds" in ele.attrib:
                if "content-desc" in ele.attrib and ele.attrib["content-desc"] != "":
                    elements.append(ele)
                elif "text" in ele.attrib and ele.attrib["text"] != "":
                    elements.append(ele)
                elif "clickable" in ele.attrib and ele.attrib["clickable"] == "true":
                    elements.append(ele)
        return elements

    def _parse_bounds(self, bounds: str) -> tuple[int, int, int, int]:
        """parse the bounds string to x1, y1, x2, y2

        Args:
            bounds (str): the bounds string

        Returns:
            tuple[int, int, int, int]: x1, y1, x2, y2
        """
        x1, y1 = bounds.split("][")[0].replace("[", "").split(",")
        x2, y2 = bounds.split("][")[1].replace("]", "").split(",")
        return int(x1), int(y1), int(x2), int(y2)

    def _calculate_iou(self, box1, box2) -> float:
        """Calculate IoU between two boxes"""
        x1_1, y1_1, x2_1, y2_1 = box1
        x1_2, y1_2, x2_2, y2_2 = box2

        # Calculate intersection
        x1_i = max(x1_1, x1_2)
        y1_i = max(y1_1, y1_2)
        x2_i = min(x2_1, x2_2)
        y2_i = min(y2_1, y2_2)

        if x2_i <= x1_i or y2_i <= y1_i:
            return 0.0

        intersection = (x2_i - x1_i) * (y2_i - y1_i)

        # Calculate union
        area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
        area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
        union = area1 + area2 - intersection

        return intersection / union

    def _rm_overlap_elements(
        self, elements: list, iou_threshold: float = 0.9
    ) -> list[ET.Element]:
        """Remove overlapped elements using NMS with IoU threshold

        Args:
            elements (list): List of elements
            iou_threshold (float): IoU threshold for NMS
        """
        if not elements:
            return []

        # Sort by y1 coordinate
        elements = sorted(
            elements, key=lambda x: self._parse_bounds(x.attrib["bounds"])[1]
        )

        # NMS
        kept_elements = []
        while len(elements) > 0:
            current = elements[0]
            kept_elements.append(current)

            current_bounds = self._parse_bounds(current.attrib["bounds"])
            elements = elements[1:]

            filtered_elements = []
            for element in elements:
                element_bounds = self._parse_bounds(element.attrib["bounds"])
                iou = self._calculate_iou(current_bounds, element_bounds)

                if iou < iou_threshold:
                    filtered_elements.append(element)

            elements = filtered_elements

        return kept_elements

    def _rm_bigger_cover_elements(self, elements: list) -> list[ET.Element]:
        """Remove elements that completely surround smaller elements

        Args:
            elements (list): List of elements with bounds attributes

        Returns:
            list[ET.Element]: Filtered elements with containers removed
        """
        if not elements:
            return []

        def get_area(element):
            x1, y1, x2, y2 = self._parse_bounds(element.attrib["bounds"])
            return (x2 - x1) * (y2 - y1)

        def is_contained(box1, box2):
            """Check if box1 is contained within box2"""
            x1_1, y1_1, x2_1, y2_1 = box1
            x1_2, y1_2, x2_2, y2_2 = box2
            return x1_2 <= x1_1 and y1_2 <= y1_1 and x2_2 >= x2_1 and y2_2 >= y2_1

        # Sort by area ascending
        elements = sorted(elements, key=get_area)

        kept_elements = []
        for i, elem in enumerate(elements):
            current_bounds = self._parse_bounds(elem.attrib["bounds"])
            is_container = False

            # Check if this element contains any smaller elements
            for smaller_elem in elements[:i]:
                smaller_bounds = self._parse_bounds(smaller_elem.attrib["bounds"])
                if is_contained(smaller_bounds, current_bounds):
                    is_container = True
                    break

            if not is_container:
                kept_elements.append(elem)

        return kept_elements

    def get_final_elements(self) -> list[dict]:
        """Get the final elements after filtering and NMS

        Returns:
            list[dict]: The final elements
        """
        elements = self._filter_elements()
        elements = self._rm_overlap_elements(elements)
        elements = self._rm_bigger_cover_elements(elements)

        elements = sorted(
            elements, key=lambda x: self._parse_bounds(x.attrib["bounds"])[1]
        )

        ret = []

        for ele in elements:
            bounds = self._parse_bounds(ele.attrib["bounds"])
            content_desc = ele.attrib.get("content-desc", "")
            text = ele.attrib.get("text", "")
            clickable = ele.attrib.get("clickable", "")
            ret.append(
                {
                    "bounds": bounds,
                    "content-desc": content_desc,
                    "text": text,
                    "clickable": clickable,
                }
            )

        return ret


class ETParserLite:
    def __init__(self, xml: str | Path) -> None:
        if isinstance(xml, str):
            self.et = ET.ElementTree(ET.fromstring(xml))
        elif isinstance(xml, Path):
            self.et = ET.parse(xml)
        self.w = int(self.et.getroot().attrib["width"])
        self.h = int(self.et.getroot().attrib["height"])

    def get_element_by_attr_value(self, attr: str, value: str) -> ET.Element:
        for el in self.et.iter():
            if attr in el.attrib and el.attrib[attr].lower() == value.lower():
                return el

    def get_element_by_attr_value_contains(self, attr: str, value: str) -> ET.Element:
        for el in self.et.iter():
            if attr in el.attrib and el.attrib[attr].lower().find(value.lower()) != -1:
                return el

    def get_element_by_conditions(self, conditions: dict) -> ET.Element:
        for el in self.et.iter():
            # Check if all conditions are met
            if all(
                el.attrib.get(attr).lower() == value.lower()
                for attr, value in conditions.items()
            ):
                return el
        return None  # Return None if no element matches

    def find_parent(self, child_element: ET.Element) -> ET.Element:
        return child_element.find("..")

    def get_bounds(element: ET.Element) -> list[int]:
        # "[1,2][3,4]" -> [1,2,3,4]
        bounds_str = element.attrib["bounds"].replace("][", ",")
        bounds_str = bounds_str.strip("[]")
        bounds = list(map(int, bounds_str.split(",")))

        return bounds


class ETParser:
    def __init__(self, xml) -> None:
        if isinstance(xml, str):
            self.et = ET.ElementTree(ET.fromstring(xml))
        elif isinstance(xml, Path):
            self.et = ET.parse(xml)
        self.w = int(self.et.getroot().attrib["width"])
        self.h = int(self.et.getroot().attrib["height"])

    def get_element(self, attr: str, name: str) -> ET.Element:
        for el in self.et.iter():
            if attr in el.attrib and el.attrib[attr].lower() == name.lower():
                return el

    def get_elements(self, xpath: str) -> list:
        """
        获取所有符合给定 XPath 的元素
        """
        # 使用 XPath 表达式找到符合条件的所有元素
        return self.et.findall(xpath)

    def get_element_contains(self, attr: str, name: str) -> ET.Element:
        for el in self.et.iter():
            if attr in el.attrib:
                if el.attrib[attr].lower().find(name.lower()) != -1:
                    return el

    def get_element_contains_from_contains(
        self, attr: str, name: str, u_attr: str, u_name: str, position: int = -1
    ) -> ET.Element:
        """
        Find the first element that contains info provided in `attr` and `name` field begin with u_attr contains u_name.

        Args:
            attr (str): Element's attribute
            name (str): Element's attribute's value
            u_attr (str): Upper limit's attribute
            u_name (str): Upper limit's attribute's value
            position (int): Confine the appearence position to the desired position. eg. We only want first position to be 5.

        Returns:
            ET.Element: Desired element
        """
        flag = False
        for el in self.et.iter():
            if (
                u_attr in el.attrib
                and el.attrib[u_attr].lower().find(u_name.lower()) != -1
                and not flag
            ):
                flag = True
                continue
            if flag:
                if position == -1:
                    if (
                        attr in el.attrib
                        and el.attrib[attr].lower().find(name.lower()) != -1
                    ):
                        return el
                else:
                    if (
                        attr in el.attrib
                        and el.attrib[attr].lower().find(name.lower()) == position
                    ):
                        return el
        # return None if nothing was found
        return None

    def get_element_contains_from_until(
        self,
        attr: str,
        name: str,
        u_attr: str,
        u_name: str,
        l_attr: str = None,
        l_name: str = None,
        position: int = -1,
    ) -> ET.Element:
        """
        Find the first element that contains info provided in `attr` and `name` field within range.

        Args:
            attr (str): Element's attribute
            name (str): Element's attribute's value
            u_attr (str): Upper limit's attribute
            u_name (str): Upper limit's attribute's value
            l_attr (str): Lower limit's attribute
            l_name (str): Lower limit's attribute's value
            position (int): Confine the appearence position to the desired position. eg. We only want first position to be 5.

        Returns:
            ET.Element: Desired element
        """
        flag = False
        for el in self.et.iter():
            if (
                u_attr in el.attrib
                and el.attrib[u_attr].lower() == u_name.lower()
                and not flag
            ):
                flag = True
            if flag:
                # meet lower limit, end finding
                if l_attr in el.attrib and el.attrib[l_attr].lower() == l_name.lower():
                    break
                if position == -1:
                    if (
                        attr in el.attrib
                        and el.attrib[attr].lower().find(name.lower()) != -1
                    ):
                        return el
                else:
                    if (
                        attr in el.attrib
                        and el.attrib[attr].lower().find(name.lower()) == position
                    ):
                        return el
        # return None if nothing was found
        return None

    def get_element_contains_from(
        self, attr: str, name: str, u_attr: str, u_name: str, position: int = -1
    ) -> ET.Element:
        """
        Find the first element that contains info provided in `attr` and `name` field within range.

        Args:
            attr (str): Element's attribute
            name (str): Element's attribute's value
            u_attr (str): Upper limit's attribute
            u_name (str): Upper limit's attribute's value
            position (int): Confine the appearence position to the desired position. eg. We only want first position to be 5.

        Returns:
            ET.Element: Desired element
        """
        flag = False
        for el in self.et.iter():
            if (
                u_attr in el.attrib
                and el.attrib[u_attr].lower() == u_name.lower()
                and not flag
            ):
                flag = True
                continue
            if flag:
                if position == -1:
                    if (
                        attr in el.attrib
                        and el.attrib[attr].lower().find(name.lower()) != -1
                    ):
                        return el
                else:
                    if (
                        attr in el.attrib
                        and el.attrib[attr].lower().find(name.lower()) == position
                    ):
                        return el
        # return None if nothing was found
        return None

    def get_element_bydic(self, conditions: dict) -> ET.Element:
        """
        Find the first element that matches all conditions provided in the `conditions` dictionary.
        :param conditions: A dictionary where keys are attribute names and values are the expected values.
        :return: The matching element or None if not found.
        """
        for el in self.et.iter():
            # Check if all conditions are met
            if all(
                attr in el.attrib and el.attrib[attr].lower() == value.lower()
                for attr, value in conditions.items()
            ):
                return el
        return None  # Return None if no element matches

    def find_parent(self, child_element: ET.Element) -> ET.Element:
        """
        手动遍历树找到父元素，因为 ElementTree 不支持 getparent()
        """
        for parent in self.et.iter():
            if child_element in parent:
                return parent
        return None

    def find_clickable_parent(self, child_element: ET.Element) -> ET.Element:
        """
        手动遍历树找到可以点击的父元素，因为 ElementTree 不支持 getparent()
        """
        if "clickable" in child_element.attrib:
            if child_element.attrib["clickable"] == "true":
                return child_element
        else:
            return None
        for parent in self.et.iter():
            if child_element in parent:
                # if parent.attrib["clickable"] == "true":
                #     return parent
                # else:
                return self.find_clickable_parent(parent)
        # return None

    def get_bounds(self, element: ET.Element) -> list[int]:
        """Get the bounds of the element

        Args:
            element (ET.Element):

        Returns:
            list[int]: [x1, y1, x2, y2]
        """

        # "[1,2][3,4]" -> [1,2,3,4]
        bounds_str = element.attrib["bounds"].replace("][", ",")

        # 1. 去掉方括号
        bounds_str = bounds_str.strip("[]")

        # 2. 将字符串按逗号分割
        bounds = list(map(int, bounds_str.split(",")))

        return bounds

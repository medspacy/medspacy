import mechanicalsoup


def mtsample_crawler(
    num_notes=100,
    index_page: str = "https://www.mtsamples.com/site/pages/browse.asp?type=91-SOAP%20/%20Chart%20/%20Progress%20Notes",
):
    """
  Get a certain number of notes from mtsamples website
  Parameters
  ----------
  num_notes : int
      The name of notes to be retrieved
  index_page : str
      start url page where the notes are listed
  """
    browser = mechanicalsoup.StatefulBrowser(user_agent="MechanicalSoup")
    browser.open(index_page)
    filter_offset = index_page.find("site/pages/browse.asp?type=")
    url_filter = index_page[filter_offset + 27 : filter_offset + 44].replace("%20", " ")
    links = []
    docs = []
    for link in browser.links():
        target = link.attrs["href"]
        if url_filter in target:
            links.append(link)
    if len(links) == 0:
        return []
    for i, link in enumerate(links):
        browser.follow_link(link)
        page = browser.get_current_page()
        # this might not work and need to be modified in the future, if mtsamples updates the html tags in note pages
        div = page.find("div", class_="hilightBold")
        if div is None:
            continue
        content = "\n".join(div.findAll(text=True, recursive=False)).strip()
        docs.append(content)
        if len(docs) >= num_notes:
            break
    return docs


# docs = mtsample_crawler(num_notes=100)
# print(docs[0])

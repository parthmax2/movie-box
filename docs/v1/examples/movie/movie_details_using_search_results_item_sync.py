# Extra imports for type hints since *_sync() methods lacks such

from movie_box.v1 import MovieDetails, Search, Session, SubjectType
from movie_box.v1.extractor.models.json import ItemJsonDetailsModel
from movie_box.v1.models import SearchResultsModel


def movie_details_using_search_results_item():
    client_session = Session()
    search = Search(
        client_session, query="avatar", subject_type=SubjectType.MOVIES
    )

    search_results: SearchResultsModel = search.get_content_model_sync()

    target_item = search_results.first_item  # (1)

    md = MovieDetails(
        target_item,
        session=client_session,
    )

    details: ItemJsonDetailsModel = md.get_content_model_sync()
    print(type(details))  # (2)


if __name__ == "__main__":
    movie_details_using_search_results_item()

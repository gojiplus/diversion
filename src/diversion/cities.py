"""Editable walking ideas grounded in official city visitor guides."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CityWalk:
    """An editorial starting point, without fabricated routes or travel times."""

    city: str
    title: str
    description: str
    origin: str
    destination: str
    stops: tuple[str, ...]
    source: str


CITY_WALKS = (
    CityWalk(
        "Paris",
        "Marais: history and food",
        (
            "Start in Place des Vosges, pause at the Carnavalet museum and "
            "Rue des Rosiers, then finish by the city hall."
        ),
        "Place des Vosges, Paris, France",
        "Hôtel de Ville, Paris, France",
        ("Musée Carnavalet, Paris, France", "Rue des Rosiers, Paris, France"),
        "https://parisjetaime.com/eng/transport/place-des-vosges-p1907",
    ),
    CityWalk(
        "Paris",
        "Montmartre: squares and art",
        (
            "Explore the hill from Abbesses through Place du Tertre and the"
            " Montmartre museum to Sacré-Cœur. Expect hills and steps."
        ),
        "Place des Abbesses, Paris, France",
        "Sacré-Cœur, Paris, France",
        ("Place du Tertre, Paris, France", "Musée de Montmartre, Paris, France"),
        "https://parisjetaime.com/eng/article/village-paris-a922",
    ),
    CityWalk(
        "Hamburg",
        "Speicherstadt to the Elbe",
        (
            "Walk between the warehouse district and HafenCity, with a "
            "maritime museum stop before the Elbphilharmonie."
        ),
        "Wasserschloss Speicherstadt, Hamburg, Germany",
        "Elbphilharmonie, Hamburg, Germany",
        ("Internationales Maritimes Museum, Hamburg, Germany",),
        "https://www.hamburg-travel.com/discover-hamburg/areas/hafencity-speicherstadt/",
    ),
    CityWalk(
        "Hamburg",
        "Alster arcades and gardens",
        (
            "Begin at the Rathaus, pass the Alster arcades and "
            "Jungfernstieg, and make the gardens of Planten un Blomen your "
            "destination."
        ),
        "Hamburger Rathaus, Hamburg, Germany",
        "Planten un Blomen, Hamburg, Germany",
        ("Alsterarkaden, Hamburg, Germany", "Jungfernstieg, Hamburg, Germany"),
        "https://www.hamburg-travel.com/see-explore/routes-tours/romantik-tour/",
    ),
    CityWalk(
        "Frankfurt",
        "Old town to the museum bank",
        (
            "From Römerberg, visit the cathedral, cross the Main on the "
            "Eiserner Steg, and finish at the Städel Museum."
        ),
        "Römerberg, Frankfurt am Main, Germany",
        "Städel Museum, Frankfurt am Main, Germany",
        (
            "Frankfurt Cathedral, Frankfurt am Main, Germany",
            "Eiserner Steg, Frankfurt am Main, Germany",
        ),
        "https://www.visitfrankfurt.travel/en/experience/discover/highlights",
    ),
    CityWalk(
        "Frankfurt",
        "Goethe and the market",
        (
            "Pair the Alte Oper with Goethe House and the Kleinmarkthalle "
            "before reaching Römerberg. Leave time for a market stop."
        ),
        "Alte Oper, Frankfurt am Main, Germany",
        "Römerberg, Frankfurt am Main, Germany",
        (
            "Goethe House, Frankfurt am Main, Germany",
            "Kleinmarkthalle, Frankfurt am Main, Germany",
        ),
        "https://www.visitfrankfurt.travel/en/experience/discover/highlights",
    ),
    CityWalk(
        "Seattle",
        "Market to Pioneer Square",
        (
            "Start at Pike Place Market, use Overlook Walk to reach the "
            "waterfront, and continue via Pier 62 toward Pioneer Square."
        ),
        "Pike Place Market, Seattle, WA",
        "Pioneer Square, Seattle, WA",
        ("Overlook Walk, Seattle, WA", "Pier 62, Seattle, WA"),
        "https://visitseattle.org/things-to-do/sightseeing/on-the-waterfront/",
    ),
    CityWalk(
        "Seattle",
        "Waterfront art and Seattle Center",
        (
            "Begin by the water at Pier 62, stop at Olympic Sculpture Park,"
            " and head inland to Seattle Center and the Space Needle."
        ),
        "Pier 62, Seattle, WA",
        "Space Needle, Seattle, WA",
        ("Olympic Sculpture Park, Seattle, WA",),
        "https://www.visitseattle.org/press/press-kit/seattles-major-attractions/",
    ),
)

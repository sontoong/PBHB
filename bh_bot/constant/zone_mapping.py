from typing import Final, TypedDict


class ZoneDict(TypedDict):
    bitvalley: str
    wintermarsh: str
    lakehaven: str
    ashvale: str
    aremore: str
    morgoroth: str
    cambora: str
    galaran: str
    eshlyn: str
    uamor: str
    melvinsgenesis: str
    zordattacks: str
    ancientodyssey: str
    southpeak: str
    fenrirsomen: str
    steamfunkcity: str
    olympiansecretparty: str
    sruxonattack: str
    galatictrials: str
    bigclaw: str


ZONES: Final[ZoneDict] = {"bitvalley": "t1", "wintermarsh": "t2",
                          "lakehaven": "t3", "ashvale": "t4", "aremore": "t5",
                          "morgoroth": "t6", "cambora": "t7", "galaran": "t8",
                          "eshlyn": "t9", "uamor": "t10", "melvinsgenesis": "t11",
                          "zordattacks": "t12", "ancientodyssey": "t13", "southpeak": "t14",
                          "fenrirsomen": "t15", "steamfunkcity": "t16",
                          "olympiansecretparty": "t17", "sruxonattack": "t18",
                          "galatictrials": "t19", "bigclaw": "t20"}

import os
import gzip
import sys
import requests
import concurrent.futures
import xml.etree.ElementTree as ET
import tkinter as tk
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from zoneinfo import ZoneInfo
import re
import html
import time
import logging

# --- KONFIGURACJA ---
OUTPUT_DIR = "Output"
FILE_RECORDER = os.path.join(OUTPUT_DIR, "epg_recorder.xml.gz")
FILE_ZGEMMA = os.path.join(OUTPUT_DIR, "epg_zgemma.xml.gz")
OVH_URL = "https://epg.ovh/plar.gz"
OTOPAY_URL = "https://iptv.otopay.io/guide.xml"
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'}
TZ = ZoneInfo("Europe/Warsaw")

# --- SŁOWNIK KANAŁÓW (Wersja zoptymalizowana - bez duplikatów i stacji radiowych) ---
CHANNELS = {
    # --- ŹRÓDŁO: ONET ---
    "13 Ulica HD": ("13-ulica-hd-509", "onet", "13UlicaHD.pl"),
    "2x2 HD": ("2x2-hd-613", "onet", "2x2HD.pl"),
    "360TuneBox": ("360tunebox-hd-304", "onet", "360TuneBoxHD.pl"),
    "4Fun Dance": ("4fun-fit-dance-244", "onet", "4FUNDANCE.pl"),
    "4Fun Kids": ("4fun-hits-283", "onet", "4FUNKIDS.pl"),
    "4Fun.TV": ("4fun-tv-269", "onet", "4FUN.TV.pl"),
    "Adventure HD": ("adventure-hd-305", "onet", "AdventureHD.pl"),
    "Ale kino+ HD": ("ale-kino-hd-262", "onet", "Alekino+HD.pl"),
    "Alfa TVP HD": ("alfa-tvp", "onet", "AlfaTVP.pl"),
    "AMC": ("mgm-hd-68", "onet", "AMCHD.pl"),
    "Animal Planet HD": ("animal-planet-niem-264", "onet", "AnimalPlanet.pl"),
    "Antena HD": ("antena", "onet", "Antena.pl"),
    "AXN Black": ("axn-black-271", "onet", "AXNBlack.pl"),
    "AXN HD": ("axn-hd-286", "onet", "AXNHD.pl"),
    "AXN Spin HD": ("axn-spin-hd-292", "onet", "AXNSpinHD.pl"),
    "AXN White": ("axn-white-272", "onet", "AXNWhite.pl"),
    "Active Family": ("active-family-hd-301", "onet", "ActiveFamilyHD.pl"),
    "Baby TV": ("baby-tv-285", "onet", "BabyTV.pl"),
    "BBC Brit HD": ("bbc-brit-hd-306", "onet", "BBCBritHD.pl"),
    "BBC Cbeebies": ("bbc-cbeebies-2", "onet", "BBCCBeebies.pl"),
    "BBC Earth HD": ("bbc-earth-hd-263", "onet", "BBCEarthHD.pl"),
    "BBC First": ("bbc-hd-261", "onet", "BBCFirst.pl"),
    "BBC Lifestyle HD": ("bbc-lifestyle-hd-542", "onet", "BBCLifestyleHD.pl"),
    "Biznes24": ("biznes24-hd-686", "onet", "Biznes24HD.pl"),
    "Blue Hustler": ("blue-hustler-280", "onet", "BlueHustler.pl"),
    "Bollywood HD": ("bollywood-hd-530", "onet", "BollywoodHD.pl"),
    "CANAL+ 1 HD": ("canal-1-hd-299", "onet", "CANAL+1HD.pl"),
    "CANAL+ 360 HD": ("canal-family-hd-297", "onet", "CANAL+360HD.pl"),
    "CANAL+ 4K ULTRA HD": ("canal-4k-ultra-hd-638", "onet", "CANAL+4KUltraHD.pl"),
    "CANAL+ DOKUMENT HD": ("canal-discovery-hd-308", "onet", "CANAL+DOKUMENTHD.pl"),
    "CANAL+ DOMO HD": ("domo-hd-437", "onet", "CANAL+DOMOHD.pl"),
    "CANAL+ FILM HD": ("canal-film-hd-278", "onet", "CANAL+FilmHD.pl"),
    "CANAL+ KUCHNIA HD": ("kuchnia-hd-434", "onet", "CANAL+KUCHNIAHD.pl"),
    "CANAL+ PREMIUM HD": ("canal-hd-288", "onet", "CANAL+PREMIUMHD.pl"),
    "CANAL+ SERIALE HD": ("canal-seriale-hd-298", "onet", "CANAL+SerialeHD.pl"),
    "CANAL+ SPORT HD": ("canal-sport-hd-12", "onet", "CANAL+SportHD.pl"),
    "CANAL+ SPORT 2 HD": ("canal-sport-2-hd-13", "onet", "CANAL+Sport2HD.pl"),
    "CANAL+ SPORT 3 HD": ("canal-sport-3-hd-676", "onet", "CANAL+Sport3HD.pl"),
    "CANAL+ SPORT 4 HD": ("canal-sport-4-hd-677", "onet", "CANAL+Sport4HD.pl"),
    "CANAL+ SPORT 5 HD": ("nsport-hd-17", "onet", "CANAL+Sport5HD.pl"),
    "Canal+ Extra 1": ("Canal+ Extra 1", "xml", "Canal+Extra1.pl"),
    "Canal+ Extra 2": ("Canal+ Extra 2", "xml", "Canal+Extra2.pl"),
    "Canal+ Extra 3": ("Canal+ Extra 3", "xml", "Canal+Extra3.pl"),
    "Canal+ Extra 4": ("Canal+ Extra 4", "xml", "Canal+Extra4.pl"),
    "Canal+ Extra 5": ("Canal+ Extra 5", "xml", "Canal+Extra5.pl"),
    "Canal+ Extra 6": ("Canal+ Extra 6", "xml", "Canal+Extra6.pl"),
    "Canal+ Extra 7": ("Canal+ Extra 7", "xml", "Canal+Extra7.pl"),
    "Canal+ Extra 8": ("Canal+ Extra 8", "xml", "Canal+Extra8.pl"),
    "Canal+ Extra 9": ("Canal+ Extra 9", "xml", "Canal+Extra9.pl"),
    "Canal+ Live 2": ("Canal+ Live 2", "xml", "Canal+Live2.pl"),
    "Canal+ Live 3": ("Canal+ Live 3", "xml", "Canal+Live3.pl"),
    "Canal+ Live 4": ("Canal+ Live 4", "xml", "Canal+Live4.pl"),
    "Canal+ Now": ("Canal+ Now", "xml", "Canal+Now.pl"),
    "Cartoon Network HD": ("cartoon-network-hd-310", "onet", "CartoonNetworkHD.pl"),
    "Cartoonito HD": ("boomerang-hd-616", "onet", "CartoonitoHD.pl"),
    "CI Polsat HD": ("ci-polsat-hd-640", "onet", "CIPolsatHD.pl"),
    "Cinemax HD": ("cinemax-hd-57", "onet", "CinemaxHD.pl"),
    "Comedy Central HD": ("comedy-central-hd-60", "onet", "ComedyCentralHD.pl"),
    "Da Vinci": ("da-vinci-hd-614", "onet", "DaVinciHD.pl"),
    "Disco Polo Music": ("disco-polo-music-191", "onet", "DiscoPoloMusic.pl"),
    "Discovery Channel": ("discovery-channel-niem-358", "onet", "DiscoveryChannel.pl"),
    "Discovery HD": ("discovery-hd-niem-450", "onet", "DiscoveryHD.pl"),
    "Discovery Historia": ("discovery-historia-54", "onet", "DiscoveryHistoria.pl"),
    "Discovery Life HD": ("discovery-life-hd-547", "onet", "DiscoveryLifeHD.pl"),
    "Discovery Science HD": ("discovery-science-hd-52", "onet", "DiscoveryScienceHD.pl"),
    "Disney Channel HD": ("disney-channel-hd-216", "onet", "DisneyChannelHD.pl"),
    "Disney Junior": ("disney-junior-469", "onet", "DisneyJunior.pl"),
    "Disney XD": ("disney-xd-235", "onet", "DisneyXD.pl"),
    "Docubox Polska": ("docubox-hd-175", "onet", "DocuBoxHD.pl"),
    "DORCEL TV HD": ("dorcel-tv-hd-660", "onet", "DorcelTVHD.pl"),
    "DTX HD": ("discovery-turbo-xtra-hd-189", "onet", "DTXHD.pl"),
    "E! Entertainment": ("e-entertainment-hd-169", "onet", "E!EntertainmentHD.pl"),
    "Eleven Sports 1 HD": ("eleven-hd-227", "onet", "ElevenSports1HD.pl"),
    "Eleven Sports 2 HD": ("eleven-hd-sports-228", "onet", "ElevenSports2HD.pl"),
    "Eleven Sports 3 HD": ("eleven-extra-hd-534", "onet", "ElevenSports3HD.pl"),
    "Eleven Sports 4 HD": ("eleven-sports-4-hd-611", "onet", "ElevenSports4HD.pl"),
    "English Club TV": ("english-club-tv-hd-181", "onet", "EnglishClubTVHD.pl"),
    "Epic Drama HD": ("epic-drama-hd-603", "onet", "EpicDramaHD.pl"),
    "Eska Rock TV": ("hip-hop-tv-511", "onet", "EskaRockTV.pl"),
    "Eska TV HD": ("eska-tv-hd-221", "onet", "EskaTVHD.pl"),
    "Eska TV Extra HD": ("eska-tv-extra-597", "onet", "EskaTVExtra.pl"),
    "Eurosport 1 Poland HD": ("eurosport-niem-366", "onet", "Eurosport1.pl"),
    "Eurosport 2 HD": ("eurosport-2-hd-120", "onet", "Eurosport2HD.pl"),
    "Eurosport 3": ("160679065", "interia", "Eurosport3.pl"),
    "Eurosport 4": ("160679413", "interia", "Eurosport4.pl"),
    "FashionBox HD": ("fashionbox-hd-171", "onet", "FashionBoxHD.pl"),
    "FightBox HD": ("fightbox-hd-453", "onet", "FightBoxHD.pl"),
    "Fightklub HD": ("fightklub-hd-168", "onet", "FightklubHD.pl"),
    "Filmax HD": ("filmax", "onet", "FILMAX.pl"),
    "FilmBox Action": ("filmbox-action-451", "onet", "FilmBoxAction.pl"),
    "FilmBox ArtHouse": ("filmbox-arthouse-hd-190", "onet", "FilmBoxArthouseHD.pl"),
    "FilmBox Extra HD": ("filmbox-extra-hd-86", "onet", "FilmBoxExtraHD.pl"),
    "FilmBox Family": ("filmbox-family-103", "onet", "FilmBoxFamily.pl"),
    "FilmBox Premium": ("filmbox-premium-85", "onet", "FilmBoxPremiumHD.pl"),
    "Fokus TV HD": ("fokus-tv-hd-47", "onet", "FokusTVHD.pl"),
    "Food Network HD": ("polsat-food-network-hd-209", "onet", "FoodNetworkHD.pl"),
    "FX Comedy HD": ("fox-comedy-hd-405", "onet", "FXComedyHD.pl"),
    "FX HD": ("fox-hd-128", "onet", "FXHD.pl"),
    "Gametoon HD": ("gametoon-hd-602", "onet", "GametoonHD.pl"),
    "Golf Zone": ("golf-channel-hd-554", "onet", "GolfZoneHD.pl"),
    "HBO HD": ("hbo-hd-26", "onet", "HBOHD.pl"),
    "HBO2 HD": ("hbo2-hd-27", "onet", "HBO2HD.pl"),
    "HBO3 HD": ("hbo-3-hd-28", "onet", "HBO3HD.pl"),
    "HGTV HD": ("hgtv-hd-558", "onet", "HGTVHD.pl"),
    "Home TV HD": ("tvr-hd-170", "onet", "HOMETVHD.pl"),
    "History HD": ("history-hd-niem-458", "onet", "HISTORYHD.pl"),
    "Hustler HD": ("hustler-hd-138", "onet", "HustlerHD.pl"),
    "ID HD": ("id-hd-188", "onet", "IDHD.pl"),
    "InUltra": ("insight-tv-uhd-682", "onet", "INULTRA.pl"),
    "Junior Music HD": ("top-kids-jr-hd-664", "onet", "JuniorMusicHD.pl"),
    "Kino Polska HD": ("kino-polska-hd-658", "onet", "KinoPolskaHD.pl"),
    "Kino Polska Muzyka": ("kino-polska-muzyka-426", "onet", "KinoPolskaMuzyka.pl"),
    "Kino TV HD": ("kino-tv-hd-663", "onet", "KinoTVHD.pl"),
    "Metro HD": ("metro-hd-536", "onet", "METROHD.pl"),
    "Mezzo": ("mezzo-234", "onet", "Mezzo.pl"),
    "Mezzo Live HD": ("mezzo-live-hd-398", "onet", "MezzoLiveHD.pl"),
    "MiniMini+ HD": ("minimini-hd-435", "onet", "MiniMini+HD.pl"),
    "Motowizja HD": ("motowizja-hd-194", "onet", "MotowizjaHD.pl"),
    "MTV Polska HD": ("mtv-polska-hd-557", "onet", "MTVPolskaHD.pl"),
    "Music Box Polska": ("music-box-hd-539", "onet", "MusicBoxHD.pl"),
    "MyZen 4K": ("myzen-4k", "onet", "MyZen4K.pl"),
    "MyZen.TV": ("myzen-tv-hd-396", "onet", "MyZen.tvHD.pl"),
    "Nat Geo People HD": ("nat-geo-people-hd-211", "onet", "NatGeoPeopleHD.pl"),
    "National Geographic HD": ("national-geographic-channel-hd-34", "onet", "NationalGeographicHD.pl"),
    "National Geographic Wild HD": ("nat-geo-wild-hd-121", "onet", "NationalGeographicWildHD.pl"),
    "Nick Jr.": ("nick-jr-hd-662", "onet", "NickJr.HD.pl"),
    "Nickelodeon": ("nickelodeon-42", "onet", "Nickelodeon.pl"),
    "Nicktoons HD": ("nicktoons-hd-631", "onet", "NicktoonsHD.pl"),
    "Novela Tv": ("novela-tv-hd-155", "onet", "NovelatvHD.pl"),
    "Novelas+ HD": ("novelas", "onet", "Novelas+.pl"),
    "Nowa TV": ("nowa-tv-hd-529", "onet", "NowaTVHD.pl"),
    "Nuta Gold HD": ("nuta-gold", "onet", "NutaGold.pl"),
    "Paramount Network Polska": ("paramount-channel-hd-65", "onet", "ParamountNetwork.pl"),
    "Planete+ HD": ("planete-hd-432", "onet", "Planete+HD.pl"),
    "Polo TV": ("polo-tv-135", "onet", "PoloTV.pl"),
    "Polonia 1 HD": ("polonia-1-328", "onet", "Polonia1.pl"),
    "Polsat HD": ("polsat-hd-35", "onet", "PolsatHD.pl"),
    "Polsat 2 HD": ("polsat-2-hd-218", "onet", "Polsat2HD.pl"),
    "Polsat Café HD": ("polsat-caf-hd-219", "onet", "PolsatCaféHD.pl"),
    "Polsat Comedy Central Extra": ("comedy-central-family-hd-612", "onet", "PolsatComedyCentralExtraHD.pl"),
    "Polsat Doku HD": ("polsat-doku-hd-551", "onet", "PolsatDokuHD.pl"),
    "Polsat Film HD": ("polsat-film-hd-162", "onet", "PolsatFilmHD.pl"),
    "Polsat Games HD": ("polsat-games-hd-670", "onet", "PolsatGamesHD.pl"),
    "Polsat JimJam": ("polsat-jimjam-89", "onet", "PolsatJimJam.pl"),
    "Polsat Music HD": ("muzo-tv-200", "onet", "PolsatMusicHD.pl"),
    "Polsat News HD": ("polsat-news-hd-229", "onet", "PolsatNewsHD.pl"),
    "Polsat News 2 HD": ("polsat-news-2-hd-671", "onet", "PolsatNews2HD.pl"),
    "Polsat News Polityka HD": ("polsat-news-polityka", "onet", "PolsatNewsPolityka.pl"),
    "Polsat Play HD": ("polsat-play-hd-22", "onet", "PolsatPlayHD.pl"),
    "Polsat Rodzina HD": ("polsat-rodzina-hd-672", "onet", "PolsatRodzinaHD.pl"),
    "Polsat Seriale HD": ("polsat-romans-173", "onet", "PolsatSeriale.pl"),
    "Polsat Sport 1": ("polsat-sport-hd-96", "onet", "PolsatSport1HD.pl"),
    "Polsat Sport 2": ("polsat-sport-extra-hd-144", "onet", "PolsatSport2HD.pl"),
    "Polsat Sport 3": ("polsat-sport-news-hd-543", "onet", "PolsatSport3HD.pl"),
    "Polsat Sport Extra 1": ("polsat-sport-premium-3-645", "onet", "PolsatSportExtra1.pl"),
    "Polsat Sport Extra 2": ("polsat-sport-premium-4-646", "onet", "PolsatSportExtra2.pl"),
    "Polsat Sport Extra 3": ("polsat-sport-premium-5-642", "onet", "PolsatSportExtra3.pl"),
    "Polsat Sport Extra 4": ("polsat-sport-premium-6-641", "onet", "PolsatSportExtra4.pl"),
    "Polsat Sport Fight HD": ("polsat-sport-fight-521", "onet", "PolsatSportFightHD.pl"),
    "Polsat Sport Premium 1": ("polsat-sport-premium-1-643", "onet", "PolsatSportPremium1.pl"),
    "Polsat Sport Premium 2": ("polsat-sport-premium-2-644", "onet", "PolsatSportPremium2.pl"),
    "Polsat Viasat Explore HD": ("polsat-viasat-explore-hd-82", "onet", "PolsatViasatExploreHD.pl"),
    "Polsat Viasat History HD": ("polsat-viasat-history-hd-71", "onet", "PolsatViasatHistoryHD.pl"),
    "Polsat Viasat Nature HD": ("polsat-viasat-nature-413", "onet", "PolsatViasatNatureHD.pl"),
    "Power TV HD": ("power-tv-hd-177", "onet", "PowerTVHD.pl"),
    "Puls 2 HD": ("puls-2-hd-199", "onet", "PULS2HD.pl"),
    "Redlight HD": ("redlight-hd-498", "onet", "RedlightHD.pl"),
    "Romance TV HD": ("romance-tv-hd-139", "onet", "RomanceTVHD.pl"),
    "STARS.TV": ("stars-tv-hd-122", "onet", "STARS.TVHD.pl"),
    "Sportklub HD": ("sportklub-hd-620", "onet", "SportklubHD.pl"),
    "Stingray CMusic HD": ("c-music-tv-260", "onet", "StingrayCMusic.pl"),
    "Stopklatka": ("stopklatka-hd-186", "onet", "STOPKLATKAHD.pl"),
    "StudioMed TV HD": ("studiomed-tv-688", "onet", "StudioMEDTV.pl"),
    "Sundance TV HD": ("sundance-channel-hd-392", "onet", "SundanceTVHD.pl"),
    "Super Polsat HD": ("super-polsat-hd-560", "onet", "SuperPolsatHD.pl"),
    "TBN Polska": ("tbn-polska-hd-621", "onet", "TBNPolskaHD.pl"),
    "Tele 5 HD": ("tele-5-niem-448", "onet", "Tele5.pl"),
    "teleTOON+ HD": ("teletoon-hd-438", "onet", "teleTOON+HD.pl"),
    "TLC HD": ("tlc-hd-163", "onet", "TLCHD.pl"),
    "Top Kids HD": ("top-kids-hd-224", "onet", "TopKidsHD.pl"),
    "Toya": ("toya-467", "onet", "TOYA.pl"),
    "Travel Channel HD": ("travel-channel-hd-152", "onet", "TravelChannelHD.pl"),
    "TravelXP 4K": ("travelxp-hd-656", "onet", "TravelxpHD.pl"),
    "TTV HD": ("ttv-33", "onet", "TTVHD.pl"),
    "TV Okazje": ("tv-okazje-hd-633", "onet", "TVOkazjeHD.pl"),
    "TV Puls HD": ("tv-puls-hd-197", "onet", "TVPulsHD.pl"),
    "TV Regio": ("tv-regio-679", "onet", "TVRegio.pl"),
    "TV Trwam HD": ("tv-trwam-108", "onet", "TVTrwam.pl"),
    "TVC HD": ("ntl-radomsko-184", "onet", "TVC.pl"),
    "TVN HD": ("tvn-hd-98", "onet", "TVNHD.pl"),
    "TVN 24 HD": ("tvn-24-hd-158", "onet", "TVN24HD.pl"),
    "TVN24 BiS HD": ("tvn-24-biznes-i-swiat-hd-537", "onet", "TVN24BiSHD.pl"),
    "TVN 7 HD": ("tvn-7-hd-142", "onet", "TVN7HD.pl"),
    "TVN Fabuła HD": ("tvn-fabula-hd-37", "onet", "TVNFabułaHD.pl"),
    "TVN Style HD": ("tvn-style-hd-141", "onet", "TVNStyleHD.pl"),
    "TVN Turbo HD": ("tvn-turbo-hd-143", "onet", "TVNTurboHD.pl"),
    "TVP 1 HD": ("tvp-1-hd-380", "onet", "TVP1HD.pl"),
    "TVP 2 HD": ("tvp-2-hd-145", "onet", "TVP2HD.pl"),
    "TVP 3 HD": ("tvp-3-172", "onet", "TVP3.pl"),
    "TVP 3 Białystok": ("tvp-3-bialystok-5", "onet", "TVP3Bialystok.pl"),
    "TVP ABC HD": ("tvp-abc-182", "onet", "TVPABC.pl"),
    "TVP Dokument HD": ("tvp-dokument", "onet", "TVPDokument.pl"),
    "TVP HD": ("tvp-hd-101", "onet", "TVPHD.pl"),
    "TVP Historia HD": ("tvp-historia-74", "onet", "TVPHistoria.pl"),
    "TVP Info": ("tvp-info-hd-525", "onet", "TVPInfoHD.pl"),
    "TVP Kobieta": ("tvp-kobieta", "onet", "TVPKobieta.pl"),
    "TVP Kultura HD": ("tvp-kultura-hd-680", "onet", "TVPKulturaHD.pl"),
    "TVP Nauka HD": ("tvp-nauka", "onet", "TVPNauka.pl"),
    "TVP Polonia": ("tvp-polonia-325", "onet", "TVPPolonia.pl"),
    "TVP Rozrywka HD": ("tvp-rozrywka-159", "onet", "TVPRozrywka.pl"),
    "TVP Seriale": ("tvp-seriale-130", "onet", "TVPSeriale.pl"),
    "TVP Sport HD": ("tvp-sport-hd-39", "onet", "TVPSportHD.pl"),
    "TVP Wilno HD": ("tvp-wilno", "onet", "TVPWilno.pl"),
    "TVP World HD": ("tvp-world", "onet", "TVPWorld.pl"),
    "TVS": ("tvs-hd-109", "onet", "TVSHD.pl"),
    "TVT": ("tvt-500", "onet", "TVT.pl"),
    "TeenNick": ("teennick", "onet", "TeenNick.pl"),
    "ViDoc TV HD": ("ctv9", "onet", "ViDocTV.pl"),
    "Vivid Red HD": ("vivid-red-hd-627", "onet", "VividREDHD.pl"),
    "Vivid Touch": ("vivid-touch-636", "onet", "VividTouch.pl"),
    "VOX Music TV": ("vox-music-tv-193", "onet", "VOXMusicTV.pl"),
    "WP HD": ("wp-hd-533", "onet", "WPHD.pl"),
    "wPolsce24 HD": ("wpolsce-pl-hd-637", "onet", "wPolsce24HD.pl"),
    "WarnerTV HD": ("tnt-hd-220", "onet", "WarnerTVHD.pl"),
    "Water Planet HD": ("water-planet-hd-156", "onet", "WaterPlanetHD.pl"),
    "Wydarzenia 24 HD": ("superstacja-hd-550", "onet", "Wydarzenia24HD.pl"),
    "Xtreme TV": ("super-tv-690", "onet", "XTREMETV.pl"),
    "Zoom TV HD": ("zoom-tv-hd-527", "onet", "ZOOMTVHD.pl"),
    "CBS Reality HD": ("CBS REALITY", "xml", "CBSReality.pl"),
    "Cinemax 2 HD": ("Cinemax 2", "xml", "Cinemax2HD.pl"),
    "Deluxe Dance": ("Deluxe Dance", "xml", "DeluxeDance.pl"),
    "Deluxe Music": ("Deluxe Music HD", "xml", "DeluxeMusicHD.pl"),
    "Dla Ciebie TV": ("Dla Ciebie TV", "xml", "DlaCiebieTV.pl"),
    "Duck TV HD": ("Duck TV", "xml", "DuckTV.pl"),
    "Duck TV Plus": ("DuckTV Plus", "xml", "DuckTVPlus.pl"),
    "Echo24": ("TV echo 24", "xml", "Echo24.pl"),
    "eSports One HD": ("eSports One HD", "xml", "eSportsOneHD.pl"),
    "Extreme Sports HD": ("Extreme Sports Channel", "xml", "ExtremeSportsHD.pl"),
    "Fast FunBox": ("fast-n-funbox-hd", "xml", "FastFunBox.pl"),
    "Fight Sports HD": ("Fight Sports HD", "xml", "FightSportsHD.pl"),
    "Film Cafe": ("Film Cafe", "xml", "FilmCafe.pl"),
    "First Music Channel HD": ("First Music Channel HD", "xml", "FirstMusicChannelHD.pl"),
    "History 2 HD": ("History 2", "xml", "History2.pl"),
    "HotBird 4K1": ("HotBird 4K1", "xml", "HotBird4K1.pl"),
    "iTVN": ("iTVN", "xml", "iTVN.pl"),
    "iTVN Extra": ("iTVN extra", "xml", "iTVNExtra.pl"),
    "Jazz TV HD": ("Jazz HD", "xml", "JazzTVHD.pl"),
    "Kanal ZERO TV": ("Kanal Zero TV", "xml", "KanalZEROTV.pl"),
    "Kapitan Bomba TV": ("Kapitan Bomba TV", "xml", "KapitanBombaTV.pl"),
    "Kujawy TV": ("TV KUJAWY", "xml", "KujawyTV.pl"),
    "Love Nature 4K": ("Love Nature 4K", "xml", "LoveNature4K.pl"),
    "Mix tape HD": ("MixTape HD", "xml", "MixTapeHD.pl"),
    "MTV 00s": ("MTV 00S", "xml", "MTV00s.pl"),
    "MTV 80s": ("MTV 80S", "xml", "MTV80s.pl"),
    "MTV 90s": ("MTV 90S", "xml", "MTV90s.pl"),
    "MTV Club": ("CLUB MTV", "xml", "MTVClub.pl"),
    "MTV Hits": ("MTV Hits", "xml", "MTVHits.pl"),
    "MTV Live HD": ("MTV Live HD", "xml", "MTVLiveHD.pl"),
    "Museum 4K": ("Museum UHD", "xml", "Museum4K.pl"),
    "Nuta TV HD": ("Nuta TV", "xml", "NutaTV.pl"),
    "Polsat Film 2 HD": ("Polsat Film 2", "xml", "PolsatFilm2HD.pl"),
    "Polsat Reality HD": ("Polsat Reality", "xml", "PolsatRealityHD.pl"),
    "Polsat X HD": ("Polsat X", "xml", "PolsatXHD.pl"),
    "Porucznik Kabura": ("Porucznik Kabura TV", "xml", "PorucznikKabura.pl"),
    "PPV HD": ("PPV", "xml", "PPVHD.pl"),
    "Prime Fight HD": ("Prime Fight HD", "xml", "PrimeFightHD.pl"),
    "Red Carpet TV International": ("Red Carpet TV International", "xml", "RedCarpetTV.pl"),
    "SciFi HD": ("SCI FI", "xml", "SciFi.pl"),
    "SkyShowtime 1": ("Skyshowtime 1", "xml", "SkyShowtime1.pl"),
    "SkyShowtime 2": ("Skyshowtime 2", "xml", "SkyShowtime2.pl"),
    "Sportowa TV": ("Sportowa.TV", "xml", "SportowaTV.pl"),
    "Szlagier TV": ("Szlagier TV", "xml", "SzlagierTV.pl"),
    "TV Biznesowa": ("TV Biznesowa", "xml", "TVBiznesowa.pl"),
    "TV4 HD": ("TV 4", "xml", "TV4.pl"),
    "TV6 HD": ("TV 6", "xml", "TV6.pl"),
    "TVC Super": ("TVC Super", "xml", "TVCSuper.pl"),
    "TVN Czas na Ślub": ("TVN Czas na Ślub Online", "xml", "TVNCzasNaSlub.pl"),
    "TVN Kryminalnie": ("TVN Kryminalnie Online", "xml", "TVNKryminalnie.pl"),
    "TVN Kulinarne Podróże": ("TVN Kulinarne Podróże Online", "xml", "TVNKulinarnePodroze.pl"),
    "TVN Kultowe Seriale": ("TVN Kultowe Seriale Online", "xml", "TVNKultoweSeriale.pl"),
    "TVN Milionerzy": ("TVN Milionerzy Online", "xml", "TVNMilionerzy.pl"),
    "TVN Momenty Prawdy": ("TVN Momenty Prawdy Online", "xml", "TVNMomentyPrawdy.pl"),
    "TVN Moto": ("TVN Moto Online", "xml", "TVNMoto.pl"),
    "TVN Patrol": ("TVN Patrol Online", "xml", "TVNPatrol.pl"),
    "TVN Pora na Show": ("TVN Pora na Show Online", "xml", "TVNPoraNaShow.pl"),
    "TVN Prawo i Życie": ("TVN Prawo i Życie Online", "xml", "TVNPrawoiZycie.pl"),
    "TVN Rajska Miłość": ("TVN Rajska Miłość Online", "xml", "TVNRajskaMilosc.pl"),
    "TVN Rewolucje w Kuchni": ("TVN Rewolucje w Kuchni Online", "xml", "TVNRewolucjeWKuchni.pl"),
    "TVN Szkoła Życia": ("TVN Szkoła Życia Online", "xml", "TVNSzkolaZycia.pl"),
    "TVN Szpitalne Historie": ("TVN Szpitalne Historie Online", "xml", "TVNSzpitalneHistorie.pl"),
    "TVN Talk Show": ("TVN Talk Show Online", "xml", "TVNTalkShow.pl"),
    "TVN Telenowele": ("TVN Telenowele Online", "xml", "TVNTelenowele.pl"),
    "TVN Usterka": ("TVN Usterka Online", "xml", "TVNUsterka.pl"),
    "TVN W Domu": ("TVN W Domu Online", "xml", "TVNWDomu.pl"),
    "TVN Życie Jak w Bajce": ("TVN Życie Jak w Bajce Online", "xml", "TVNZycieJakWBajce.pl"),
    "TVP ABC 2 HD": ("TVP ABC 2", "xml", "TVPABC2.pl"),
    "TVP Historia 2": ("TVP Historia 2", "xml", "TVPHistoria2.pl"),
    "TVP Kultura 2 HD": ("TVP Kultura 2", "xml", "TVPKultura2.pl"),
    "Twoja TV": ("TWOJA TV", "xml", "TwojaTV.pl"),
    "VOD 205": ("VOD 205", "xml", "VOD205.pl"),
    "VOD 206": ("VOD 206", "xml", "VOD206.pl"),
    "VOD 207": ("VOD 207", "xml", "VOD207.pl"),
    "VOD 208": ("VOD 208", "xml", "VOD208.pl"),
    "Viaplay Sports 1": ("Viaplay Sports 1", "xml", "ViaplaySports1.pl"),
    "Viaplay Sports 2": ("Viaplay Sports 2", "xml", "ViaplaySports2.pl"),
    "Viasat True Crime": ("Viasat True Crime", "xml", "ViasatTrueCrime.pl"),
}

def clean_xml_text(text):
    if not text: return ""
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)
    return html.escape(text)

class EPGMerger:
    def __init__(self):
        self.all_programmes = []
        self.added_events = {}  # (ch_id, start): has_desc (bool)
        self.now = datetime.now(TZ)
        self.stats = {"ok": 0, "errors": 0, "skipped": 0}
        
        if not os.path.exists(OUTPUT_DIR): 
            os.makedirs(OUTPUT_DIR)
            
        # Poprawiona konfiguracja logowania: FileHandler zamiast FileHeader
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(OUTPUT_DIR, "build_log.txt"), encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        logging.info("--- START NOWEJ SESJI EPG ---")

    def load_history(self):
        """Wczytuje historię i informuje o postępach[cite: 1]."""
        if not os.path.exists(FILE_RECORDER): 
            logging.info("Brak pliku historii. Rozpoczynam od zera.")
            return False
            
        limit = self.now - timedelta(hours=96)
        try:
            with gzip.open(FILE_RECORDER, 'rb') as f:
                tree = ET.parse(f)
                count = 0
                for prog in tree.findall("programme"):
                    st_str = prog.get("start")[:14]
                    st_dt = datetime.strptime(st_str, "%Y%m%d%H%M%S").replace(tzinfo=TZ)
                    if st_dt >= limit:
                        ch_id, start = prog.get("channel"), prog.get("start")
                        has_desc = prog.find("desc") is not None
                        self.all_programmes.append(prog)
                        self.added_events[(ch_id, start)] = has_desc
                        count += 1
                logging.info(f"Wczytano {count} audycji z historii (Catchup -96h).")
            return True
        except Exception as e: 
            logging.error(f"Błąd analizy bazy: {e}")
            return False

    def get_onet_details(self, url):
        time.sleep(0.05) # Ochrona przed błędem 429
        
        # Przygotowujemy pusty słownik na wszystkie metadane
        details = {
            "desc": "", "icon": "", "category": "", "countries": [],
            "year": "", "duration_min": None, "age_rating": "",
            "star_rating": "", "directors": [], "actors": []
        }
        
        try:
            r = requests.get(f"https://programtv.onet.pl{url}", headers=HEADERS, timeout=10)
            if r.status_code != 200: 
                return details
                
            s = BeautifulSoup(r.text, 'lxml')

            # 1. Opis
            desc_p = s.find('p', class_='entryDesc')
            if desc_p: details["desc"] = desc_p.get_text(strip=True)

            # 2. Właściwy Plakat (celujemy precyzyjnie w sekcję obrazka głównego)
            img_section = s.find('section', class_='colLeft img-placeholder')
            if img_section:
                img = img_section.find('img')
                if img and img.get('src'):
                    src = img['src']
                    details["icon"] = f"https:{src}" if src.startswith('//') else src

            # 3. Kategoria wiekowa (PEGI)
            header = s.find('header', class_='headerArt')
            if header:
                pegi_span = header.find('span', class_=re.compile(r'pegi\d+'))
                if pegi_span:
                    m = re.search(r'pegi(\d+)', ' '.join(pegi_span.get('class', [])))
                    if m: details["age_rating"] = m.group(1)

            # 4. Kategoria, czas trwania, kraj i rok
            type_span = s.find('span', class_='type')
            if type_span: details["category"] = type_span.get_text(strip=True)

            time_span = s.find('span', class_='time')
            if time_span:
                time_text = time_span.get_text(strip=True) # np. Kanada, Luksemburg 2014, 120 min
                
                # Wyciągamy rok
                year_match = re.search(r'\b((?:19|20)\d{2})\b', time_text)
                if year_match: details["year"] = year_match.group(1)
                
                # Wyciągamy czas trwania do obliczenia "stop"
                dur_match = re.search(r'(\d+)\s*min', time_text)
                if dur_match: details["duration_min"] = int(dur_match.group(1))
                
                # Wyciągamy kraje
                if year_match:
                    countries_part = time_text[:year_match.start()].strip(' ,')
                    if countries_part:
                        details["countries"] = [c.strip() for c in countries_part.split(',')]

            # 5. Ocena w gwiazdkach
            stars_span = s.find('span', class_=re.compile(r'stars\d+'))
            if stars_span:
                m = re.search(r'stars(\d+)', ' '.join(stars_span.get('class', [])))
                if m: details["star_rating"] = f"{m.group(1)}/5"

            # 6. Reżyseria i Obsada
            cast_ul = s.find('ul', class_='cast')
            if cast_ul:
                items = cast_ul.find_all('li')
                current_header = ""
                for li in items:
                    if 'header' in li.get('class', []):
                        current_header = li.get_text(strip=True).lower()
                    else:
                        text = li.get_text(strip=True)
                        if not text: continue
                        if 'reżyseria' in current_header:
                            details["directors"].extend([d.strip() for d in text.split(',') if d.strip()])
                        elif 'obsada' in current_header:
                            details["actors"].extend([a.strip() for a in text.split(',') if a.strip()])

            return details
            
        except Exception as e:
            return details

    def get_interia_details(self, url):
        try:
            r = requests.get(url if url.startswith('http') else f"https://programtv.interia.pl{url}", headers=HEADERS, timeout=10)
            s = BeautifulSoup(r.text, 'lxml')
            div = s.find('div', id='intertext1')
            if div:
                if div.find('strong', class_='type'): div.find('strong', class_='type').decompose()
                return div.get_text(separator=" ", strip=True)
            return ""
        except: return ""

    def process_channel(self, name, ident, src, epg_id, selected_days, detailed_days):
        """Pobiera dane dla kanału i buduje ustrukturyzowane tagi XMLTV."""
        results = []
        for d in selected_days:
            is_detailed = (d in detailed_days)
            mode_str = "PEŁNE" if is_detailed else "OGÓLNE"
            logging.info(f"[{src.upper()}] Przetwarzanie: {name} (Dzień {d:+d}) - Tryb: {mode_str}")
            
            base_date = (self.now + timedelta(days=d)).replace(hour=0, minute=0, second=0, microsecond=0)
            
            try:
                if src == 'onet':
                    url = f"https://programtv.onet.pl/program-tv/{ident}?dzien={d}&pelny-dzien=1"
                    r = requests.get(url, headers=HEADERS, timeout=15)
                    
                    if r.status_code != 200:
                        logging.error(f"  -> Błąd połączenia z Onet (Kod: {r.status_code})")
                        self.stats["errors"] += 1
                        continue

                    items = BeautifulSoup(r.text, 'lxml').find_all('li')
                    prog_count = 0
                    
                    for item in items:
                        if not item.find('div', class_='titles'): continue
                        
                        h, m = map(int, item.find('span', class_='hour').text.split(':'))
                        start_dt = base_date + timedelta(hours=h, minutes=m)
                        
                        # Pobieramy dynamiczną strefę czasową
                        tz_offset = start_dt.strftime("%z")
                        start_str = start_dt.strftime(f"%Y%m%d%H%M00 {tz_offset}")
                        
                        if self.added_events.get((epg_id, start_str)) == True and not is_detailed:
                            continue

                        title_a = item.find('div', class_='titles').find('a')
                        title_text = clean_xml_text(title_a.text)
                        
                        # Budowa głównego tagu programme
                        prog = ET.Element("programme", start=start_str, channel=epg_id)
                        
                        details = {}
                        if is_detailed and title_a.get('href'):
                            details = self.get_onet_details(title_a.get('href'))
                        
                        # Obliczanie i dodawanie czasu stop
                        dur_min = details.get("duration_min")
                        if dur_min:
                            stop_dt = start_dt + timedelta(minutes=dur_min)
                            stop_tz = stop_dt.strftime("%z")
                            stop_str = stop_dt.strftime(f"%Y%m%d%H%M00 {stop_tz}")
                            prog.set("stop", stop_str)

                        # Tytuł
                        ET.SubElement(prog, "title", lang="pl").text = title_text
                        
                        # Opis
                        desc_text = details.get("desc", "")
                        if desc_text: ET.SubElement(prog, "desc", lang="pl").text = clean_xml_text(desc_text)
                        
                        # Obsada (Credits)
                        actors = details.get("actors", [])
                        directors = details.get("directors", [])
                        if actors or directors:
                            credits_el = ET.SubElement(prog, "credits")
                            for d in directors:
                                ET.SubElement(credits_el, "director").text = clean_xml_text(d)
                            for a in actors:
                                ET.SubElement(credits_el, "actor").text = clean_xml_text(a)

                        # Data (Rok)
                        year = details.get("year", "")
                        if year: ET.SubElement(prog, "date").text = year
                        
                        # Kategoria
                        category = details.get("category", "")
                        if category: ET.SubElement(prog, "category", lang="pl").text = clean_xml_text(category)
                        
                        # Ikona
                        icon_url = details.get("icon", "")
                        if icon_url: ET.SubElement(prog, "icon", src=icon_url)

                        # Kraje
                        countries = details.get("countries", [])
                        if countries:
                            c_str = ",".join([f'"{c}"' for c in countries]) # Format: "Kanada","USA"
                            ET.SubElement(prog, "country", lang="pl").text = clean_xml_text(c_str)

                        # Rating wiekowy (PEGI)
                        age_rating = details.get("age_rating", "")
                        if age_rating:
                            rating_el = ET.SubElement(prog, "rating")
                            ET.SubElement(rating_el, "value").text = age_rating

                        # Ocena w gwiazdkach
                        star_rating = details.get("star_rating", "")
                        if star_rating:
                            star_el = ET.SubElement(prog, "star-rating")
                            ET.SubElement(star_el, "value").text = star_rating

                        results.append(prog)
                        self.added_events[(epg_id, start_str)] = is_detailed
                        prog_count += 1
                    
                    logging.info(f"  -> OK: Pobrano {prog_count} audycji")
                    self.stats["ok"] += 1

                elif src == 'interia':
                    url = f"https://programtv.interia.pl/stacja-x,cid,{ident},data,{base_date.strftime('%Y-%m-%d')}?from=mobile"
                    r = requests.get(url, headers=HEADERS, timeout=15)
                    
                    if r.status_code != 200:
                        logging.error(f"  -> Błąd połączenia z Interia (Kod: {r.status_code})")
                        self.stats["errors"] += 1
                        continue

                    soup = BeautifulSoup(r.text, 'lxml')
                    items = soup.find_all('div', class_='item-wrap')
                    prog_count = 0
                    
                    for item in items:
                        time_div = item.find('div', class_='emission-time')
                        if not time_div: continue
                        
                        h, m = map(int, time_div.text.strip().split(':'))
                        start_dt = base_date + timedelta(hours=h, minutes=m)
                        
                        tz_offset = start_dt.strftime("%z")
                        start_str = start_dt.strftime(f"%Y%m%d%H%M00 {tz_offset}")

                        if self.added_events.get((epg_id, start_str)) == True and not is_detailed:
                            continue

                        title_a = item.find('a', class_='title')
                        title_text = clean_xml_text(title_a.get('title'))
                        
                        prog = ET.Element("programme", start=start_str, channel=epg_id)
                        ET.SubElement(prog, "title", lang="pl").text = title_text
                        
                        if is_detailed:
                            # Proste pobieranie szczegółów z Interii (tekst i ewentualnie kategoria)
                            detail_url = title_a.get('href')
                            if detail_url:
                                full_url = detail_url if detail_url.startswith('http') else f"https://programtv.interia.pl{detail_url}"
                                try:
                                    det_r = requests.get(full_url, headers=HEADERS, timeout=10)
                                    det_s = BeautifulSoup(det_r.text, 'lxml')
                                    div = det_s.find('div', id='intertext1')
                                    if div:
                                        type_strong = div.find('strong', class_='type')
                                        if type_strong:
                                            first_word = type_strong.find('span', class_='first-word')
                                            if first_word:
                                                # Usuń nawiasy jeśli są w tekście (np. "(mistrzostwa)")
                                                cat_text = first_word.get_text(strip=True).strip('()')
                                                ET.SubElement(prog, "category", lang="pl").text = clean_xml_text(cat_text)
                                            type_strong.decompose()
                                        
                                        desc_text = div.get_text(separator=" ", strip=True)
                                        if desc_text:
                                            ET.SubElement(prog, "desc", lang="pl").text = clean_xml_text(desc_text)
                                except Exception as e:
                                    pass # Cicha porażka dla pojedynczego detalu

                        results.append(prog)
                        self.added_events[(epg_id, start_str)] = is_detailed
                        prog_count += 1
                    
                    logging.info(f"  -> OK: Pobrano {prog_count} audycji (Interia)")
                    self.stats["ok"] += 1

            except Exception as e:
                logging.error(f"  -> Błąd krytyczny kanału {name}: {e}")
                self.stats["errors"] += 1
        return results

    def run(self, selected_days, detailed_days):
        """Koordynuje pobieranie z systemem Fallback dla EPG zewnętrznego."""
        logging.info(f"Rozpoczynam pobieranie dla dni: {selected_days}")
        start_count = len(self.all_programmes)
        
        # 1. Główne źródła: Onet i Interia (Wielowątkowo)
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            # Puszczamy parser tylko dla źródeł 'onet' i 'interia'
            futures = [executor.submit(self.process_channel, n, i, s, eid, selected_days, detailed_days) 
                       for n, (i, s, eid) in CHANNELS.items() if s in ['onet', 'interia']]
            for f in concurrent.futures.as_completed(futures):
                self.all_programmes.extend(f.result())

        # Zabezpieczenie Fallback (Dla Interii i kanałów XML)
        # my_epg_ids to wszystkie unikalne ID (trzeci parametr), do których chcemy przypisać EPG
        my_epg_ids = {v[2] for v in CHANNELS.values()}

        # 2. Uzupełnianie z zewnętrznych list XML (Normalizator / Fallback)
        EXTERNAL_SOURCES = [
            OVH_URL, 
            OTOPAY_URL,
            "https://raw.githubusercontent.com/darthvader1971rn-collab/EPG-Onet-Full/main/Output/epg_recorder.xml.gz",
            "https://raw.githubusercontent.com/darthvader1971rn-collab/EPG-Onet-Full/main/Output/epg_zgemma.xml.gz"
        ]
        
        logging.info(f"Sprawdzanie źródeł zewnętrznych ({len(EXTERNAL_SOURCES)} źródeł)...")
        xml_added = 0
        
        for idx, url in enumerate(EXTERNAL_SOURCES, 1):
            try:
                logging.info(f"[*] Pobieranie EPG ze źródła [{idx}/{len(EXTERNAL_SOURCES)}]: {url}")
                r = requests.get(url, headers=HEADERS, timeout=30, allow_redirects=True)
                
                if r.status_code != 200:
                    logging.warning(f"  [!] Pominięto: Serwer zwrócił kod {r.status_code}")
                    continue
                
                try:
                    content = gzip.decompress(r.content) if url.endswith(".gz") else r.content
                    ext_xml = ET.fromstring(content)
                except Exception as parse_err:
                    logging.warning(f"  [!] Błąd formatu danych (nie XML/GZ): {parse_err}")
                    continue

                for p in ext_xml.findall("programme"):
                    cid = p.get("channel")
                    start = p.get("start")
                    
                    # LOGIKA FALLBACK / NORMALIZATORA
                    # Sprawdzamy czy:
                    # 1. Pobrany kanał jest na naszej liście (cid in my_epg_ids)
                    # 2. Nie mamy jeszcze audycji o tej godzinie dla tego kanału (!in added_events)
                    # To ratuje nas, gdy Interia dla Eurosportu np. wyrzuci błąd i nie doda eventów.
                    if cid and start and cid in my_epg_ids and (cid, start) not in self.added_events:
                        
                        # NORMALIZACJA: Wymuszamy dodanie języka "pl" dla zgodności z formatem OVH
                        for tag in ['title', 'desc', 'category']:
                            el = p.find(tag)
                            if el is not None and not el.get('lang'):
                                el.set('lang', 'pl')
                                
                        self.all_programmes.append(p)
                        # Oznaczamy, że dodaliśmy EPG, więc kolejne pliki XML nie nadpiszą już tej audycji
                        self.added_events[(cid, start)] = p.find("desc") is not None
                        xml_added += 1
                        
            except Exception as e:
                import traceback
                logging.error(f"  [!] SZCZEGÓŁOWY BŁĄD Fuzji EPG z {url}:")
                logging.error("\n" + traceback.format_exc())

        # 3. Podsumowanie sesji
        end_count = len(self.all_programmes)
        new_items = end_count - start_count
        
        logging.info("="*50)
        logging.info("PODSUMOWANIE SESJI:")
        logging.info(f" - Przetworzone kanały główne (Onet/Interia): {self.stats['ok']} OK, {self.stats['errors']} Błędów")
        logging.info(f" - Nowo pobrane audycje (Portal): {new_items - xml_added}")
        logging.info(f" - Uzupełnione z list XML (np. Otopay/OVH): {xml_added}")
        logging.info(f" - Całkowita liczba audycji w bazie: {end_count}")
        logging.info("="*50)

    def save(self):
        limit_zgemma = (self.now + timedelta(days=7)).strftime("%Y%m%d%H%M%S")
        
        def build(filter_z=False):
            root = ET.Element("tv", {
                "generator-info-name": "EPG-Hybrid-Grabber", 
                "generator-info-url": "https://epg.ovh"
            })
            
            # --- GENERATOR ALIASÓW (Super Matching System) ---
            # Buduje dziesiątki różnych wariantów nazw dla jednego kanału,
            # aby aplikacje IPTV zawsze mogły dopasować EPG do listy M3U.
            for name, (_, _, eid) in CHANNELS.items():
                ch = ET.SubElement(root, "channel", id=eid)
                
                # Słownik do przechowywania unikalnych, sformatowanych nazw
                unique_names = set()
                
                # Wzorce do generowania (Na podstawie logiki OVH)
                patterns = [
                    "{base}",
                    "PL: {base}",
                    "PL: {base} HD",
                    "PL: {base} FHD",
                    "PL| {base}",
                    "PL| {base} HD",
                    "{base} PL",
                    "{base} HD PL",
                    "{base} FHD PL",
                    "{base} HD",
                    "{base} FHD",
                    "{base} sd",
                    "{base} [PL]"
                ]
                
                # Funkcja czyszcząca nazwę z dopisków jakości przed generowaniem
                # (żeby z "Polsat HD" nie zrobić "Polsat HD HD")
                clean_base = re.sub(r'(?i)\s+(HD|FHD|4K|UHD|SD)$', '', name).strip()
                
                # Generujemy wszystkie kombinacje
                for pattern in patterns:
                    # Dodajemy wariant z czystą nazwą (np. "Polsat HD" -> "PL: Polsat HD")
                    unique_names.add(pattern.format(base=clean_base))
                
                # Dodajemy do XML unikalne warianty wygenerowane z szablonów
                for display_name in sorted(unique_names):
                    ET.SubElement(ch, "display-name", lang="pl").text = display_name
                
                # Wymuszamy dodanie oryginalnej nazwy ze słownika, jeśli nie ma jej na liście
                # i dodajemy unikalne ID dostawcy EPG (np. "Alekino+HD.pl"),
                # na którym często bazują aplikacje typu Smart IPTV.
                custom_names = [name, eid]
                for custom_name in custom_names:
                    if custom_name not in unique_names:
                        ET.SubElement(ch, "display-name", lang="pl").text = custom_name
                        unique_names.add(custom_name)
                        
            # Dodawanie audycji do struktury
            for p in self.all_programmes:
                if filter_z and p.get("start")[:14] > limit_zgemma: 
                    continue
                root.append(p)
                
            # Formatowanie estetyczne drzewa XML
            if hasattr(ET, "indent"):
                ET.indent(root)
                
            # Generowanie stringa XML
            xml_bytes = ET.tostring(root, encoding='utf-8', xml_declaration=True)
            xml_str = xml_bytes.decode('utf-8')
            
            # Wstrzykiwanie DOCTYPE w standardzie OVH (XMLTV)
            xml_str = xml_str.replace("?>", "?>\n<!DOCTYPE tv SYSTEM \"xmltv.dtd\">", 1)
            
            return xml_str.encode('utf-8')

        logging.info("Zapisywanie plików EPG do archiwum...")
        
        with gzip.open(FILE_RECORDER, 'wb') as f: 
            f.write(build(False))
            
        with gzip.open(FILE_ZGEMMA, 'wb') as f: 
            f.write(build(True))
            
        logging.info("Zapis zakończony sukcesem!")

    def format_time(self, dt):
        return dt.strftime("%Y%m%d%H%M00 +0100")

# --- GUI ---
def start_gui():
    root = tk.Tk()
    root.title("EPG Multi-Source Grabber")
    root.geometry("350x650")
    
    # Tryb "Pobierz wszystko"
    all_mode = tk.BooleanVar(value=False)
    tk.Checkbutton(root, text="POBIERZ WSZYSTKO (Start projektu)", variable=all_mode, font=('Arial', 10, 'bold'), fg="red").pack(pady=10)
    
    tk.Label(root, text="Lub wybierz dni ręcznie (Szczegółowo):", font=('Arial', 9)).pack()
    
    vars_dict = {}
    # Zakres dni 0-12 (standardowe okno EPG)
    for i in range(0, 13):
        # Domyślnie zaznaczone tylko dni 1 i 12
        v = tk.BooleanVar(value=(i in [1, 12]))
        tk.Checkbutton(root, text=f"Dzień +{i}", variable=v).pack(anchor='w', padx=100)
        vars_dict[i] = v

    def launch():
        # Zczytujemy z GUI wszystkie dni, przy których widnieje "ptaszek"
        checked_days = [d for d, v in vars_dict.items() if v.get()]

        if all_mode.get():
            # "Pobierz wszystko" ZAZNACZONE:
            # - wywołujemy wszystkie dni z listy (od 0 do 12)
            # - PEŁNE EPG dostają tylko te zaznaczone, reszta to OGÓLNE
            selected = list(vars_dict.keys())
            detailed = checked_days
        else:
            # "Pobierz wszystko" ODZNACZONE:
            # - wywołujemy tylko zaznaczone dni (domyślnie 1 i 12, plus to co doklikasz)
            # - wszystkie wywołane dostają PEŁNE EPG
            selected = checked_days
            detailed = checked_days
            
        root.destroy()
        m = EPGMerger()
        m.load_history()
        m.run(selected, detailed)
        m.save()
        print("Gotowe!")

    tk.Button(root, text="URUCHOM", bg="green", fg="white", font=('Arial', 10, 'bold'), command=launch).pack(pady=20, fill='x', padx=30)
    root.mainloop()

if __name__ == "__main__":
    if "--auto" in sys.argv:
        m = EPGMerger()
        m.load_history()
        # GitHub (Tryb auto): Zgodnie z wytycznymi, na serwerze wystarczy tylko 1 i 12 (pełne)
        m.run(selected_days=[0, 1, 12], detailed_days=[0, 1, 12])
        m.save()
    else:
        start_gui()

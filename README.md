# Satellite Ground Station Communication 🛰️

## Présentation du projet
Ce projet consiste en la finalisation d'une station sol de communication satellite réalisée à l'Université de Rennes 1. L'objectif est de permettre la poursuite automatique et la réception de données de satellites civils en orbite basse (LEO).

## Fonctionnalités clés
* **Prédiction Orbitale** : Développement d'un système de prédiction de mécanique orbitale pour les satellites ciblés (logiciel GPredict).
* **Pilotage Matériel** : Contrôle d'un moteur Yaesu GS-5500 via plusieurs dispositifs d'asservissement.
* **Traitement de Signal** : Démodulation des signaux reçus pour l'extraction de données de télémétrie.

## Technologies utilisées
* **Logiciels** : GPredict, GNU Radio, Python.
* **Hardware** : SDR (Software Defined Radio), Raspberry Pi, Arduino, Moteur Yaesu GS-5500.
* **Concepts** : Mécatronique, Asservissement, Traitement de signal.

## Architecture du système
[Image de l'architecture du système : Antenne -> SDR -> Traitement GNU Radio -> Client GPredict]

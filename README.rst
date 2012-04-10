.. -*- coding: utf-8 -*-

Brouz is an accounting web application, specifically tailored for
French freelancers. This is why the rest of this documentation is in
French and the English terms used in the user interface do not make
sense.

Brouz is written by Damien Baty and is licensed under the 3-clause BSD
license, a copy of which is included in the source.


Documentation en français
=========================

**État du code :** fonctionnel mais pas encore complètement testé en
« situation réelle ».

Brouz est une application web permettant de lister les recettes et
dépenses, en les ventilant par catégorie. L'objectif est de faciliter
la « déclaration contrôlée » que je dois établir en France en tant
qu'entreprise individuelle (profession libérale). Je ne suis pas (du
tout) un spécialiste de la comptabilité et je ne garantis absolument
pas la conformité de Brouz avec la loi française. En utilisant Brouz,
vous vous engagez à :

- ne pas me poursuivre en justice ou dans la rue si l'administration
  fiscale mange votre chien et confisque votre Lamborghini à cause
  d'une erreur de calcul dans Brouz;

- m'envoyer un petit mot si l'application vous est utile, si vous avez
  corrigé des erreurs (notamment dans la logique de calcul des
  recettes, dépenses et taxes).


Fonctionnalités
===============

Brouz permet :

- de saisir une transaction unique : j'appelle transaction unique une
  transaction dont tous les composants tombent dans une seule
  "catégorie fiscale". Par exemple, la facturation (par vous) d'une
  prestation classique, ou bien le paiement (par vous) d'une
  prestation classique ;

- de saisir une transaction composite, qui est composée de lignes
  multiples pouvant avoir plusieurs catégories fiscales. Par exemple :

  - la CSG : une partie de la CSG est déductible, l'autre non. Dans ce
    cas, vous aurez une transaction composite qui inclue une ligne
    pour chaque partie de la CSG, incombant chacune à une catégorie
    différente,

  - le paiement, en une seule fois, d'un ordinateur rentrant dans la
    catégorie des immobilisations et de fournitures informatiques
    rentrant, elles, dans la catégorie « Petit outillage » ou «
    Fournitures de bureau » ;

- d'établir un rapport annuel des recettes et dépenses, ventilées par
  catégories, ainsi qu'un calcul de la TVA à déclarer. Ce rapport
  reprend les mêmes intitulés que les formulaires 2035-AK et 2035-BK.

Attention : Brouz n'inclut pas toutes les catégories mentionnées dans
les formulaires 2035-AK et 2035-BK. Je n'ai inclus que celles dont
j'avais besoin. Cependant, ajouter d'autres catégories devraient être
relativement simple (cf. ``brouz/models.py``).


Licence
=======

Brouz est publié sous la licence BSD à 3 clauses, inclue dans les
sources.
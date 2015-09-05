# -*- coding: utf-8 -*-

# OMG, I am writing code in French!


PLUS_VALUES = 0
RECETTES = 0 + PLUS_VALUES
DOTATION_AMORTISSEMENTS = 0
TVA_PAYEE_EN_2013 = 0
TVA_SUPPL_2013 = 0  # restant dû après acompte de décembre 2013
BASE_FP = 0
BASE_CSG_DEDUCTIBLE = 0
BASE_CHARGES_SOCIALES_PERSONNELLES = 0
BASE_DEPENSES = 0


def calc_rsi(benefs):
    return int(6.50/100 * benefs)

def calc_urssaf(benefs, csp):
    csg_crds = int(8/100.0 * (benefs + csp))
    return {
        'fp': 93,
        'af': int(5.4/100 * benefs),
        'csg_crds': csg_crds,
        'csg_deductible': int(csg_crds * 5.1/8)}

def calc_cipav(benefs):
    return 0  # compte CIPAV soldé au 31/12/2013


charges_sociales_personnelles = BASE_CHARGES_SOCIALES_PERSONNELLES
fp = BASE_FP
csg_deductible = BASE_CSG_DEDUCTIBLE
urssaf = None
rsi = None
derniers_benefs = 0  # pour détecter la convergence
tva_totale = TVA_PAYEE_EN_2013  # initialisé ici pour la 0ème itération

for i in range(0, 100):  # large, au cas où je me loupe et que ça ne converge pas :)
    benefs = RECETTES - (BASE_DEPENSES + fp + csg_deductible + charges_sociales_personnelles + DOTATION_AMORTISSEMENTS + tva_totale)
    print "---"
    print u"Itération : %d" % i
    print u"Recettes : %d" % RECETTES
    print u"FP : %d" % fp
    print u"CSG déductible : %d" % csg_deductible
    print u"Charges sociales personnelles : %d" % charges_sociales_personnelles
    print u"RSI : %s" % rsi
    print u"URSSAF : %s" % urssaf
    print u"Bénéfices : %d" % benefs
    tva_totale = TVA_PAYEE_EN_2013 + TVA_SUPPL_2013
    urssaf = calc_urssaf(benefs, charges_sociales_personnelles)
    cipav = calc_cipav(benefs)
    rsi = calc_rsi(benefs)
    csg_deductible = BASE_CSG_DEDUCTIBLE + urssaf['csg_deductible']
    charges_sociales_personnelles = BASE_CHARGES_SOCIALES_PERSONNELLES + rsi + urssaf['af'] + cipav
    fp = BASE_FP + urssaf['fp']
    if abs(benefs - derniers_benefs) <= 1:
        break
    derniers_benefs = benefs

print "==="
print u"Provision TVA: %d" % TVA_SUPPL_2013
print u"TVA totale (ligne 11): %d (base) + %d (provision) = %d" % (TVA_PAYEE_EN_2013, TVA_SUPPL_2013, tva_totale)
print "Provision FP : %d" % urssaf['fp']
print "Total FP : %d (base) + %d (provision) = %d" % (
    BASE_FP,
    urssaf['fp'],
    fp)
print "Provision RSI : %d" % rsi
print "Provision AF : %d" % urssaf['af']
print "Provision CIPAV : %d" % cipav
print "Total charges sociales personnelles : %d (base) + %d (provision) = %d" % (
    BASE_CHARGES_SOCIALES_PERSONNELLES,
    rsi + urssaf['af'] + cipav,
    charges_sociales_personnelles)
total_csg_deductible = BASE_CSG_DEDUCTIBLE + urssaf['csg_deductible']
print "Total CSG déductible : %d (base) + %d (provision) = %d" % (
    BASE_CSG_DEDUCTIBLE,
    urssaf['csg_deductible'],
    total_csg_deductible)
depenses_finales = BASE_DEPENSES + fp + charges_sociales_personnelles + total_csg_deductible + tva_totale
print "Total dépenses : %d" % depenses_finales
print "Bénéfice final : %d" % (RECETTES - depenses_finales - DOTATION_AMORTISSEMENTS)

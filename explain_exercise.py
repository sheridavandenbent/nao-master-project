def explain_exercise(level=None, first_number=None, second_number=None):
    over = (first_number % 10) < (second_number % 10)

    number_of_units = second_number % 10
    number_of_tens = int((second_number - number_of_units) / 10)
    first_nr_explanation = first_number
    second_nr_explanation = second_number

    explanation = ['Dit is hoe ik de som ' + str(first_nr_explanation) + ' min ' + str(second_nr_explanation) + ' op heb gelost. Ik moet van het getal ' + str(first_nr_explanation) + ' er ' + str(second_nr_explanation) + ' afhalen.']

    if level == 1 or level == 2:
        explanation.append('Ik begin met 10 eraf.')
        explanation.append(str(first_nr_explanation) + ' min 10 is ' + str(first_nr_explanation - 10) + '.')
        number_of_tens -= 1
        first_nr_explanation -= 10

        for i in range(number_of_tens):
            explanation.append('Dan haal ik er nog een keer 10 van af.')
            explanation.append(str(first_nr_explanation) + ' min 10 is ' + str(first_nr_explanation - 10) + '.')
            first_nr_explanation -= 10

        if number_of_units == 1:
            explanation.append('Dan heb ik alle tientallen eraf gehaald. Nu de eenheden. Dat is er ' + str(number_of_units) + '.')
        else:
            explanation.append('Dan heb ik alle tientallen eraf gehaald. Nu de eenheden. Dat zijn er ' + str(number_of_units)  + '.')

        if over:
            units_first_number = first_number % 10
            units_to_go_under = number_of_units - units_first_number

            explanation.append('Ik spring eerst van ' + str(first_nr_explanation) + ' naar het tiental. Dus haal ik er eerst ' + str(units_first_number) + ' af.')
            explanation.append(str(first_nr_explanation) + ' min ' + str(units_first_number) + ' is ' + str(first_nr_explanation - units_first_number) + '.')

            first_nr_explanation -= units_first_number

            explanation.append('Van de ' + str(number_of_units) + ' heb ik er nu ' + str(units_first_number) + ' afgehaald. Nu moeten er dus nog ' + str(units_to_go_under) + ' af.')
            explanation.append(str(first_nr_explanation) + ' min ' + str(units_to_go_under) + ' is ' + str(first_nr_explanation - units_to_go_under) + '.')

            first_nr_explanation -= units_to_go_under

        else:
            explanation.append(str(first_nr_explanation) + ' min ' + str(number_of_units) + ' is ' + str(first_nr_explanation - number_of_units) + '.')

            first_nr_explanation -= number_of_units



    if level == 3:
        explanation.append('Ik begin met de tientallen. Dat is ' + str(number_of_tens * 10) + '.')
        explanation.append(str(first_nr_explanation) + ' min ' + str(number_of_tens * 10) + ' is ' + str(first_nr_explanation - (number_of_tens * 10)) + '.')

        first_nr_explanation -= (number_of_tens * 10)

        if number_of_units == 1:
            explanation.append('Dan heb ik alle tientallen eraf gehaald. Nu de eenheden. Dat is er ' + str(number_of_units) + '.')
        else:
            explanation.append('Dan heb ik alle tientallen eraf gehaald. Nu de eenheden. Dat zijn er ' + str(number_of_units)  + '.')

        if over:
            units_first_number = first_number % 10
            units_to_go_under = number_of_units - units_first_number

            explanation.append('Ik spring eerst van ' + str(first_nr_explanation) + ' naar het tiental. Dus haal ik er eerst ' + str(units_first_number) + ' af.')
            explanation.append(str(first_nr_explanation) + ' min ' + str(units_first_number) + ' is ' + str(first_nr_explanation - units_first_number) + '.')

            first_nr_explanation -= units_first_number

            explanation.append('Van de ' + str(number_of_units) + ' heb ik er nu ' + str(units_first_number) + ' afgehaald. Nu moeten er dus nog ' + str(units_to_go_under) + ' af.')
            explanation.append(str(first_nr_explanation) + ' min ' + str(units_to_go_under) + ' is ' + str(first_nr_explanation - units_to_go_under) + '.')

            first_nr_explanation -= units_to_go_under

        else:
            explanation.append(str(first_nr_explanation) + ' min ' + str(number_of_units) + ' is ' + str(first_nr_explanation - number_of_units) + '.')

            first_nr_explanation -= number_of_units



    if level == 4:
        explanation.append('Ik begin met de tientallen. Dat is ' + str(number_of_tens * 10) + '.')
        explanation.append(str(first_nr_explanation) + ' min ' + str(number_of_tens * 10) + ' is ' + str(first_nr_explanation - (number_of_tens * 10)) + '.')

        first_nr_explanation -= (number_of_tens * 10)


        if number_of_units == 1:
            explanation.append('Daarna haal ik de eenheden eraf. Dat is er ' + str(number_of_units) + '.')
        else:
            explanation.append('Daarna haal ik de eenheden eraf. Dat zijn er ' + str(number_of_units) + '.')

        explanation.append(str(first_nr_explanation) + ' eraf ' + str(number_of_units) + ' is ' + str(first_nr_explanation - number_of_units) + '.')

        first_nr_explanation -= number_of_units


    explanation.append('Het antwoord is dus ' + str(first_nr_explanation) + '.')



    return ' '.join(explanation)

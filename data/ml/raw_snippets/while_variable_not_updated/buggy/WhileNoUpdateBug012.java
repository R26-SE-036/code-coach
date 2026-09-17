package data.ml.raw_snippets.while_variable_not_updated.buggy;

public class WhileNoUpdateBug012 {
    static int findFirstNegative(int[] numbers) {
        boolean found = false;
        int position = -1;
        while (!found) {
            position++;
            if (numbers[position] < 0) {
                System.out.println("Negative at " + position);
            }
        }
        return position;
    }
}

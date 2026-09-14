package data.ml.raw_snippets.while_variable_not_updated.fixed;

public class WhileNoUpdateFix028 {
    static double average(int[] marks, int count) {
        int i = 0;
        double sum = 0;
        while (i < count) {
            sum += marks[i];
            i++;
        }
        return sum / count;
    }
}

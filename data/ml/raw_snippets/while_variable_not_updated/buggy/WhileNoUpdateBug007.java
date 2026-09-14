package data.ml.raw_snippets.while_variable_not_updated.buggy;

public class WhileNoUpdateBug007 {
    static void printAll(int[] values) {
        int index = 0;
        while (index < values.length) {
            System.out.println(values[index]);
        }
    }
}

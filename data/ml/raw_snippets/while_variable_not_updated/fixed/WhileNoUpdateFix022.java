package data.ml.raw_snippets.while_variable_not_updated.fixed;

public class WhileNoUpdateFix022 {
    static boolean contains(int[] data, int target) {
        boolean found = false;
        int i = 0;
        while (!found && i < data.length) {
            found = data[i] == target;
            i++;
        }
        return found;
    }
}

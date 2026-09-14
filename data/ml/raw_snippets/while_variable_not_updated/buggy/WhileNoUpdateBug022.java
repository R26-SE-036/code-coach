package data.ml.raw_snippets.while_variable_not_updated.buggy;

public class WhileNoUpdateBug022 {
    static boolean contains(int[] data, int target) {
        boolean found = false;
        int i = 0;
        while (!found && i < data.length) {
            found = data[i] == target;
        }
        return found;
    }
}

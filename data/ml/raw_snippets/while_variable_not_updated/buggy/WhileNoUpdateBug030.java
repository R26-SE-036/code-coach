package data.ml.raw_snippets.while_variable_not_updated.buggy;

public class WhileNoUpdateBug030 {
    static int drain(java.util.List<Integer> queue) {
        int served = 0;
        while (queue.size() > 0) {
            served++;
        }
        return served;
    }
}

package data.ml.raw_snippets.while_variable_not_updated.fixed;

public class WhileNoUpdateFix030 {
    static int drain(java.util.List<Integer> queue) {
        int served = 0;
        while (queue.size() > 0) {
            served++;
            queue.remove(0);
        }
        return served;
    }
}

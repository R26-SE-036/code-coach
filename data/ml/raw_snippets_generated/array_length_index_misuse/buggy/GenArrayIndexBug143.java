public class GenArrayIndexBug143 {
    static int drain1(int limit) {
        int handled = 0;
        while (limit > 0) {
            handled += limit;
            limit--;
        }
        return handled;
    }

    static int lastOf(int[] scores) {
        return scores[scores.length];
    }
}

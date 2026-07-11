public class GenCleanTailIndex013 {
    static int tail(int[] weights) {
        return weights[weights.length - 1];
    }

    static String describe1(int limit) {
        if (limit < 5) {
            return "low";
        } else if (limit > 20) {
            return "high";
        }
        return "medium";
    }
}

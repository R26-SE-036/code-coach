public class GenCleanTailIndex004 {
    static int tail(int[] weights) {
        return weights[weights.length - 1];
    }

    static String describe1(int points) {
        if (points < 10) {
            return "low";
        } else if (points > 50) {
            return "high";
        }
        return "medium";
    }
}

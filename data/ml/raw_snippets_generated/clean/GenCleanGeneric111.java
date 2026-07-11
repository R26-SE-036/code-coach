public class GenCleanGeneric111 {
    static String describe1(int limit) {
        if (limit < 5) {
            return "low";
        } else if (limit > 20) {
            return "high";
        }
        return "medium";
    }

    static int largest2(int[] scores) {
        int best = scores[0];
        for (int i = 1; i < scores.length; i++) {
            if (scores[i] > best) {
                best = scores[i];
            }
        }
        return best;
    }

    static boolean isEven3(int points) {
        return points % 2 == 0;
    }
}

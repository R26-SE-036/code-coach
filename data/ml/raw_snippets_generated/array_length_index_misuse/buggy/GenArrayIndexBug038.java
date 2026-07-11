public class GenArrayIndexBug038 {
    static void stampLast(int[] scores, int value) {
        scores[scores.length] = value;
    }

    static int largest1(int[] scores) {
        int best = scores[0];
        for (int i = 1; i < scores.length; i++) {
            if (scores[i] > best) {
                best = scores[i];
            }
        }
        return best;
    }

    static int average2(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static void printAll3(int[] totals) {
        for (int value : totals) {
            System.out.println(value);
        }
    }

    static boolean isEven4(int quota) {
        return quota % 2 == 0;
    }

    static String describe5(int level) {
        if (level < 5) {
            return "low";
        } else if (level > 20) {
            return "high";
        }
        return "medium";
    }
}

public class GenCleanBoundaryMinusOne026 {
    static int largest1(int[] ratings) {
        int best = ratings[0];
        for (int i = 1; i < ratings.length; i++) {
            if (ratings[i] > best) {
                best = ratings[i];
            }
        }
        return best;
    }

    static boolean isEven2(int stock) {
        return stock % 2 == 0;
    }

    static boolean isEven3(int stock) {
        return stock % 2 == 0;
    }

    static int tally(int[] scores) {
        int total = 0;
        for (int i = 0; i <= scores.length - 1; i++) {
            total += scores[i];
        }
        return total;
    }

    static String describe4(int quota) {
        if (quota < 5) {
            return "low";
        } else if (quota > 20) {
            return "high";
        }
        return "medium";
    }

    static void printAll5(int[] stocks) {
        for (int value : stocks) {
            System.out.println(value);
        }
    }

    static int sum6(int[] marks) {
        int total = 0;
        for (int i = 0; i < marks.length; i++) {
            total += marks[i];
        }
        return total;
    }
}

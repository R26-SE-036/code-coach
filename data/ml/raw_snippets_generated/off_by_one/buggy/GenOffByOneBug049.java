public class GenOffByOneBug049 {
    static boolean isEven1(int quota) {
        return quota % 2 == 0;
    }

    static void show(int[] sizes) {
        for (int i = 0; i <= sizes.length; i++) {
            System.out.println(sizes[i]);
        }
    }

    static String describe2(int steps) {
        if (steps < 10) {
            return "low";
        } else if (steps > 50) {
            return "high";
        }
        return "medium";
    }

    static int largest3(int[] ratings) {
        int best = ratings[0];
        for (int i = 1; i < ratings.length; i++) {
            if (ratings[i] > best) {
                best = ratings[i];
            }
        }
        return best;
    }

    static int clamp4(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static int sum5(int[] marks) {
        int total = 0;
        for (int i = 0; i < marks.length; i++) {
            total += marks[i];
        }
        return total;
    }
}

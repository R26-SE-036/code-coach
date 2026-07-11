public class GenOffByOneFix075 {
    static boolean isEven1(int steps) {
        return steps % 2 == 0;
    }

    static String describe2(int steps) {
        if (steps < 100) {
            return "low";
        } else if (steps > 500) {
            return "high";
        }
        return "medium";
    }

    static int[] duplicate(int[] ratings) {
        int[] copy = new int[ratings.length];
        for (int i = 0; i < ratings.length; i++) {
            copy[i] = ratings[i];
        }
        return copy;
    }

    static boolean isEven3(int points) {
        return points % 2 == 0;
    }
}

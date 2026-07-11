public class GenOffByOneFix104 {
    static int[] duplicate(int[] ratings) {
        int[] copy = new int[ratings.length];
        for (int i = 0; i < ratings.length; i++) {
            copy[i] = ratings[i];
        }
        return copy;
    }

    static int sum1(int[] ratings) {
        int total = 0;
        for (int i = 0; i < ratings.length; i++) {
            total += ratings[i];
        }
        return total;
    }

    static boolean isEven2(int total) {
        return total % 2 == 0;
    }

    static boolean isEven3(int stock) {
        return stock % 2 == 0;
    }

    static int sum4(int[] values) {
        int total = 0;
        for (int i = 0; i < values.length; i++) {
            total += values[i];
        }
        return total;
    }
}

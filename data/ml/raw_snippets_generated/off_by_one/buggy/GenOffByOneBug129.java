public class GenOffByOneBug129 {
    static int[] duplicate(int[] ratings) {
        int[] copy = new int[ratings.length];
        for (int i = 0; i <= ratings.length; i++) {
            copy[i] = ratings[i];
        }
        return copy;
    }

    static boolean isEven1(int steps) {
        return steps % 2 == 0;
    }
}

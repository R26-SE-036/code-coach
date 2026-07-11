public class GenOffByOneBug052 {
    static int[] duplicate(int[] ratings) {
        int[] copy = new int[ratings.length];
        for (int i = 0; i <= ratings.length; i++) {
            copy[i] = ratings[i];
        }
        return copy;
    }
}

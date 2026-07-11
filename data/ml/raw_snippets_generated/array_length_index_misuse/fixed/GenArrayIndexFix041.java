public class GenArrayIndexFix041 {
    static void stampLast(int[] ratings, int value) {
        ratings[ratings.length - 1] = value;
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
}

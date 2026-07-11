public class GenArrayIndexBug041 {
    static void stampLast(int[] ratings, int value) {
        ratings[ratings.length] = value;
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

public class GenArrayIndexBug066 {
    static void stampLast(int[] scores, int value) {
        scores[scores.length] = value;
    }
}

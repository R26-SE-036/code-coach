public class GenArrayIndexBug042 {
    static void stampLast(int[] scores, int value) {
        scores[scores.length] = value;
    }
}

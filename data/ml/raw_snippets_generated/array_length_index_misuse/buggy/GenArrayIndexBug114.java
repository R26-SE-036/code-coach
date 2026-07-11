public class GenArrayIndexBug114 {
    static void stampLast(int[] scores, int value) {
        scores[scores.length] = value;
    }
}

public class GenArrayIndexBug069 {
    static void stampLast(int[] scores, int value) {
        scores[scores.length] = value;
    }
}

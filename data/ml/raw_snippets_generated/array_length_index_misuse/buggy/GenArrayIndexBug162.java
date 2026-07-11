public class GenArrayIndexBug162 {
    static void stampLast(int[] ratings, int value) {
        ratings[ratings.length] = value;
    }
}

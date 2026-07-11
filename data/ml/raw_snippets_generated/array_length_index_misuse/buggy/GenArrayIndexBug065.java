public class GenArrayIndexBug065 {
    static void stampLast(int[] ratings, int value) {
        ratings[ratings.length] = value;
    }
}

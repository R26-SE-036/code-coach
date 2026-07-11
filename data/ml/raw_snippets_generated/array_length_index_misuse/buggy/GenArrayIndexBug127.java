public class GenArrayIndexBug127 {
    static void stampLast(int[] marks, int value) {
        marks[marks.length] = value;
    }
}

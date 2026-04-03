public class ArrayIndexBug017 {
    public int getLastMark(int[] marks) {
        int last = marks[marks.length];
        return last;
    }
}
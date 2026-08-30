// VIVA DEMO FILE - starts deliberately broken. See docs/VIVA_PLAN.md.
//
// Act 1: three syntax errors. The Java language server underlines them RED.
//        Code Coach reports nothing - it cannot reason about code that does
//        not parse.
// Act 2: fix the three syntax errors. The red clears, the file compiles, and
//        Code Coach underlines line 18 YELLOW - the loop reads one past the
//        end of the array.
// Act 3: change <= to < . The yellow clears.
//
// To reset between runs: bash docs/viva-reset.sh
public class VivaDemo {
    public static void main(String[] args) {
        int[] marks = {70, 55, 88, 92}

        int total = 0;

        for (int i = 0; i <= marks.length; i++ {
            total = total + marks[i];
        }

        System.out.println("Total: " + total);
    }

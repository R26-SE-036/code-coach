package data.ml.raw_snippets.while_variable_not_updated.fixed;

public class WhileNoUpdateFix017 {
    static int meetingPoint(int left, int right) {
        int moves = 0;
        while (left < right) {
            moves += 2;
            left++;
            right--;
        }
        return moves;
    }
}
